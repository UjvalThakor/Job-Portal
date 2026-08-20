import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count

from candidates.models import Candidate, Resume
from candidates.services.validation import validate_resume_file, ValidationError as FileValidationError
from candidates.services.pipeline import process_resume, PipelineError
from jobs.models import JobDescription, Analysis, InterviewQuestion
from jobs.services.analyze import run_analysis
from jobs.services.matching import rank_candidates


def _serialize_candidate(c):
    return {
        'id': c.pk,
        'full_name': c.full_name or f"Candidate #{c.pk}",
        'email': c.email,
        'phone': c.phone,
        'address': c.address,
        'skills': c.skills or [],
        'education': c.education or [],
        'certifications': c.certifications or [],
        'experience': c.experience or [],
        'projects': c.projects or [],
        'languages': c.languages or [],
        'total_experience_years': c.total_experience_years,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '',
    }


def _serialize_job(j):
    # Deterministic metadata for salary, work mode, job type, and company
    salary_min = int(j.min_experience_years * 3 + 6)
    salary_max = int(j.min_experience_years * 4 + 12)
    work_modes = ['Remote', 'Hybrid', 'On-site']
    job_types = ['Full-time', 'Part-time', 'Internship', 'Fresher']
    
    # Pick deterministic work mode and job type based on ID
    work_mode = work_modes[j.pk % len(work_modes)]
    job_type = job_types[(j.pk * 2) % len(job_types)]
    company_name = f"{j.department or 'Enterprise'} Technologies" if j.department else "Core Tech Solutions"

    return {
        'id': j.pk,
        'title': j.title,
        'company': company_name,
        'department': j.department or 'Engineering',
        'description': j.description,
        'required_skills': j.required_skills or [],
        'preferred_skills': j.preferred_skills or [],
        'min_experience_years': j.min_experience_years,
        'work_mode': work_mode,
        'job_type': job_type,
        'salary_range': f"₹{salary_min}–{salary_max} LPA",
        'location': 'Bengaluru, IN • Hybrid' if work_mode == 'Hybrid' else ('Remote (Global)' if work_mode == 'Remote' else 'Mumbai, IN'),
        'created_at': j.created_at.strftime('%Y-%m-%d %H:%M') if j.created_at else '',
        'analyses_count': j.analyses.count(),
    }


def _serialize_analysis(a):
    return {
        'id': a.pk,
        'candidate_id': a.candidate.pk,
        'candidate_name': a.candidate.full_name or f"Candidate #{a.candidate.pk}",
        'candidate_email': a.candidate.email,
        'job_id': a.job.pk,
        'job_title': a.job.title,
        'company': f"{a.job.department or 'Enterprise'} Technologies",
        'ats_score': round(a.ats_score, 1),
        'match_score': round(a.match_score, 1),
        'matched_skills': a.matched_skills or [],
        'missing_skills': a.missing_skills or [],
        'summary': a.summary,
        'strengths': a.strengths or [],
        'concerns': a.concerns or [],
        'analyzer_source': a.analyzer_source,
        'created_at': a.created_at.strftime('%Y-%m-%d %H:%M') if a.created_at else '',
        'status': 'Shortlisted' if a.match_score >= 75 else ('Under Review' if a.match_score >= 50 else 'Applied'),
    }


def api_dashboard(request):
    stats = {
        'total_candidates': Candidate.objects.count(),
        'total_resumes': Resume.objects.count(),
        'total_jobs': JobDescription.objects.count(),
        'total_analyses': Analysis.objects.count(),
        'avg_ats_score': round(Analysis.objects.aggregate(avg=Avg('ats_score'))['avg'] or 0, 1),
        'avg_match_score': round(Analysis.objects.aggregate(avg=Avg('match_score'))['avg'] or 0, 1),
        'failed_resumes': Resume.objects.filter(status='failed').count(),
        'ocr_resumes': Resume.objects.filter(ocr_used=True).count(),
        'profile_completion': 92,
    }

    top_analyses = Analysis.objects.select_related('candidate', 'job').order_by('-match_score')[:10]
    recent_jobs = JobDescription.objects.annotate(n=Count('analyses')).order_by('-created_at')[:10]
    recent_resumes = Resume.objects.order_by('-uploaded_at')[:8]

    # Sample Companies
    companies = [
        {'id': 1, 'name': 'Enterprise AI Corp', 'industry': 'Software & AI', 'size': '500-1000 employees', 'location': 'Bengaluru, IN', 'open_jobs': 12, 'rating': 4.8},
        {'id': 2, 'name': 'CloudScale Innovations', 'industry': 'Cloud & DevOps', 'size': '200-500 employees', 'location': 'Remote / San Francisco', 'open_jobs': 8, 'rating': 4.9},
        {'id': 3, 'name': 'FinTech Dynamics', 'industry': 'Financial Technology', 'size': '1000+ employees', 'location': 'Mumbai, IN', 'open_jobs': 15, 'rating': 4.6},
        {'id': 4, 'name': 'CyberShield Security', 'industry': 'Cybersecurity', 'size': '100-250 employees', 'location': 'Hyderabad, IN', 'open_jobs': 6, 'rating': 4.7},
    ]

    return JsonResponse({
        'stats': stats,
        'top_candidates': [_serialize_analysis(a) for a in top_analyses],
        'recent_jobs': [_serialize_job(j) for j in recent_jobs],
        'companies': companies,
        'recent_resumes': [{
            'id': r.pk,
            'filename': r.original_filename or r.file.name,
            'candidate_name': r.candidate.full_name if r.candidate else 'Unassigned',
            'status': r.status,
            'ocr_used': r.ocr_used,
            'uploaded_at': r.uploaded_at.strftime('%Y-%m-%d %H:%M') if r.uploaded_at else '',
        } for r in recent_resumes]
    })


def api_jobs_list(request):
    jobs = JobDescription.objects.order_by('-created_at')
    return JsonResponse({'jobs': [_serialize_job(j) for j in jobs]})


@csrf_exempt
def api_job_create(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        required_skills = [s.strip() for s in data.get('required_skills', '').split(',') if s.strip()] if isinstance(data.get('required_skills'), str) else data.get('required_skills', [])
        preferred_skills = [s.strip() for s in data.get('preferred_skills', '').split(',') if s.strip()] if isinstance(data.get('preferred_skills'), str) else data.get('preferred_skills', [])

        job = JobDescription.objects.create(
            title=data.get('title', 'Untitled Job'),
            department=data.get('department', 'Engineering'),
            description=data.get('description', ''),
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            min_experience_years=float(data.get('min_experience_years', 0)),
        )
        return JsonResponse({'success': True, 'job': _serialize_job(job)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def api_job_detail(request, pk):
    job = get_object_or_404(JobDescription, pk=pk)
    ranked = rank_candidates(job)
    analyzed_candidate_ids = set(job.analyses.values_list('candidate_id', flat=True))
    unanalyzed = Candidate.objects.exclude(id__in=analyzed_candidate_ids).order_by('-created_at')

    ranked_list = []
    for a in ranked:
        c = a.candidate
        ranked_list.append({
            'analysis_id': a.pk,
            'candidate': _serialize_candidate(c),
            'ats_score': round(a.ats_score, 1),
            'match_score': round(a.match_score, 1),
            'matched_skills': a.matched_skills or [],
            'missing_skills': a.missing_skills or [],
            'summary': a.summary,
            'strengths': a.strengths or [],
            'concerns': a.concerns or [],
            'status': 'Shortlisted' if a.match_score >= 75 else ('Under Review' if a.match_score >= 50 else 'Applied'),
        })

    return JsonResponse({
        'job': _serialize_job(job),
        'ranked_candidates': ranked_list,
        'unanalyzed_candidates': [_serialize_candidate(c) for c in unanalyzed],
    })


@csrf_exempt
def api_job_apply(request, job_pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    job = get_object_or_404(JobDescription, pk=job_pk)
    
    candidate_id = request.POST.get('candidate_id')
    full_name = request.POST.get('full_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    files = request.FILES.getlist('file') or request.FILES.getlist('files')

    if not candidate_id and request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            candidate_id = data.get('candidate_id')
            full_name = data.get('full_name', '')
            email = data.get('email', '')
        except Exception:
            pass

    try:
        candidate = None
        resume = None

        if candidate_id:
            candidate = get_object_or_404(Candidate, pk=candidate_id)
            resume = candidate.resumes.order_by('-uploaded_at').first()
        elif email:
            candidate = Candidate.objects.filter(email=email).first()
            if candidate:
                resume = candidate.resumes.order_by('-uploaded_at').first()

        if files:
            f = files[0]
            validate_resume_file(f)
            if not candidate and email:
                candidate, _ = Candidate.objects.get_or_create(
                    email=email,
                    defaults={'full_name': full_name, 'phone': phone}
                )
            resume = Resume.objects.create(
                candidate=candidate,
                file=f,
                original_filename=f.name,
                file_size=f.size,
                status='validated',
            )
            cand = process_resume(resume, django_file=f)
            if cand:
                candidate = cand

        if not candidate:
            return JsonResponse({'error': 'Please select a candidate profile or upload a resume file.'}, status=400)

        analysis = run_analysis(candidate, job, resume=resume)

        return JsonResponse({
            'success': True,
            'candidate': _serialize_candidate(candidate),
            'analysis': _serialize_analysis(analysis),
            'message': f"Application submitted successfully for {job.title}!"
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def api_candidates_list(request):
    candidates = Candidate.objects.order_by('-created_at')
    return JsonResponse({'candidates': [_serialize_candidate(c) for c in candidates]})


def api_candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    resumes = candidate.resumes.order_by('-uploaded_at')
    analyses = candidate.analyses.select_related('job').order_by('-match_score')

    return JsonResponse({
        'candidate': _serialize_candidate(candidate),
        'resumes': [{
            'id': r.pk,
            'filename': r.original_filename or r.file.name,
            'file_url': r.file.url if r.file else '',
            'status': r.status,
            'raw_text': r.raw_text,
            'ocr_used': r.ocr_used,
            'uploaded_at': r.uploaded_at.strftime('%Y-%m-%d %H:%M') if r.uploaded_at else '',
        } for r in resumes],
        'analyses': [_serialize_analysis(a) for a in analyses],
    })


@csrf_exempt
def api_candidate_edit(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    candidate = get_object_or_404(Candidate, pk=pk)
    try:
        data = json.loads(request.body)
        candidate.full_name = data.get('full_name', candidate.full_name)
        candidate.email = data.get('email', candidate.email)
        candidate.phone = data.get('phone', candidate.phone)
        candidate.address = data.get('address', candidate.address)
        if 'skills' in data:
            candidate.skills = [s.strip() for s in data['skills'].split(',')] if isinstance(data['skills'], str) else data['skills']
        if 'total_experience_years' in data:
            candidate.total_experience_years = float(data['total_experience_years'])
        candidate.save()
        return JsonResponse({'success': True, 'candidate': _serialize_candidate(candidate)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def api_upload_resumes(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    files = request.FILES.getlist('files')
    if not files:
        return JsonResponse({'error': 'No files uploaded'}, status=400)

    created_candidates = []
    errors = []

    for f in files:
        try:
            validate_resume_file(f)
        except FileValidationError as e:
            errors.append(f"{f.name}: {str(e)}")
            continue

        resume = Resume.objects.create(
            file=f,
            original_filename=f.name,
            file_size=f.size,
            status='validated',
        )
        try:
            cand = process_resume(resume, django_file=f)
            created_candidates.append(_serialize_candidate(cand))
        except PipelineError as e:
            errors.append(f"{f.name}: {str(e)}")

    return JsonResponse({
        'success': len(created_candidates) > 0,
        'created_count': len(created_candidates),
        'failed_count': len(errors),
        'errors': errors,
        'candidates': created_candidates
    })


@csrf_exempt
def api_analyze_candidate(request, job_pk, candidate_pk):
    job = get_object_or_404(JobDescription, pk=job_pk)
    candidate = get_object_or_404(Candidate, pk=candidate_pk)
    resume = candidate.resumes.order_by('-uploaded_at').first()
    analysis = run_analysis(candidate, job, resume=resume)
    return JsonResponse({'success': True, 'analysis': _serialize_analysis(analysis)})


@csrf_exempt
def api_analyze_all(request, job_pk):
    job = get_object_or_404(JobDescription, pk=job_pk)
    analyzed_candidate_ids = set(job.analyses.values_list('candidate_id', flat=True))
    candidates = Candidate.objects.exclude(id__in=analyzed_candidate_ids)
    count = 0
    for candidate in candidates:
        resume = candidate.resumes.order_by('-uploaded_at').first()
        if resume:
            run_analysis(candidate, job, resume=resume)
            count += 1
    return JsonResponse({'success': True, 'analyzed_count': count})


def api_analysis_detail(request, pk):
    analysis = get_object_or_404(Analysis.objects.select_related('candidate', 'job'), pk=pk)
    questions = analysis.questions.all()

    return JsonResponse({
        'analysis': _serialize_analysis(analysis),
        'candidate': _serialize_candidate(analysis.candidate),
        'job': _serialize_job(analysis.job),
        'questions': [{
            'id': q.pk,
            'category': q.category,
            'question': q.question,
            'sample_answer': q.sample_answer,
            'rationale': q.rationale,
        } for q in questions]
    })


@csrf_exempt
def api_evaluate_answers(request, analysis_pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    analysis = get_object_or_404(Analysis, pk=analysis_pk)
    questions = {q.pk: q for q in analysis.questions.all()}

    try:
        data = json.loads(request.body)
        user_answers = data.get('answers', {})

        results = []
        total_score = 0
        count = 0

        for q_id_str, answer_text in user_answers.items():
            q_id = int(q_id_str)
            if q_id not in questions:
                continue

            q = questions[q_id]
            ans_clean = (answer_text or '').strip()
            ans_lower = ans_clean.lower()

            if not ans_clean:
                score = 0
                feedback = "No answer provided."
                status = "unanswered"
            else:
                word_count = len(ans_clean.split())
                sample_lower = (q.sample_answer or '').lower()

                key_terms = set(word.strip('.,()') for word in sample_lower.split() if len(word) > 4)
                matched_terms = [t for t in key_terms if t in ans_lower]
                term_ratio = len(matched_terms) / max(1, len(key_terms))

                base_score = min(100, word_count * 2.5 + term_ratio * 60)
                score = round(max(30, min(98, base_score)), 1)

                if score >= 80:
                    feedback = "Excellent! Clear technical depth and architecture concepts demonstrated."
                    status = "excellent"
                elif score >= 55:
                    feedback = "Good response. Covers core concepts; consider adding performance metrics or trade-offs."
                    status = "good"
                else:
                    feedback = "Basic response. Elaborate more on practical implementation details and challenges."
                    status = "needs_work"

            results.append({
                'question_id': q.pk,
                'category': q.category,
                'question': q.question,
                'user_answer': ans_clean,
                'score': score,
                'status': status,
                'feedback': feedback,
                'sample_answer': q.sample_answer,
            })

            total_score += score
            count += 1

        overall_score = round(total_score / max(1, count), 1)

        return JsonResponse({
            'success': True,
            'overall_score': overall_score,
            'results': results,
            'candidate_name': analysis.candidate.full_name,
            'job_title': analysis.job.title,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
