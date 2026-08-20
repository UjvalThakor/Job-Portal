from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import JobDescription, Analysis
from .forms import JobDescriptionForm
from .services.analyze import run_analysis
from .services.matching import rank_candidates
from candidates.models import Candidate


def job_list(request):
    jobs = JobDescription.objects.order_by('-created_at')
    return render(request, 'jobs/list.html', {'jobs': jobs})


def job_create(request):
    if request.method == 'POST':
        form = JobDescriptionForm(request.POST)
        if form.is_valid():
            job = form.save()
            messages.success(request, f"Job '{job.title}' created.")
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobDescriptionForm()
    return render(request, 'jobs/form.html', {'form': form, 'is_edit': False})


def job_edit(request, pk):
    job = get_object_or_404(JobDescription, pk=pk)
    if request.method == 'POST':
        form = JobDescriptionForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated.")
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobDescriptionForm(instance=job)
    return render(request, 'jobs/form.html', {'form': form, 'is_edit': True, 'job': job})


def job_detail(request, pk):
    job = get_object_or_404(JobDescription, pk=pk)
    ranked = rank_candidates(job)
    analyzed_candidate_ids = set(job.analyses.values_list('candidate_id', flat=True))
    unanalyzed = Candidate.objects.exclude(id__in=analyzed_candidate_ids).order_by('-created_at')
    return render(request, 'jobs/detail.html', {
        'job': job, 'ranked': ranked, 'unanalyzed': unanalyzed,
    })


def analyze_candidate(request, job_pk, candidate_pk):
    job = get_object_or_404(JobDescription, pk=job_pk)
    candidate = get_object_or_404(Candidate, pk=candidate_pk)
    resume = candidate.resumes.order_by('-uploaded_at').first()
    run_analysis(candidate, job, resume=resume)
    messages.success(request, f"Analysis complete for {candidate.full_name or candidate}.")
    return redirect('jobs:detail', pk=job_pk)


def analyze_all(request, job_pk):
    job = get_object_or_404(JobDescription, pk=job_pk)
    analyzed_candidate_ids = set(job.analyses.values_list('candidate_id', flat=True))
    candidates = Candidate.objects.exclude(id__in=analyzed_candidate_ids)
    count = 0
    for candidate in candidates:
        resume = candidate.resumes.order_by('-uploaded_at').first()
        if resume:
            run_analysis(candidate, job, resume=resume)
            count += 1
    messages.success(request, f"Ran analysis for {count} candidate(s).")
    return redirect('jobs:detail', pk=job_pk)


def analysis_detail(request, pk):
    analysis = get_object_or_404(Analysis.objects.select_related('candidate', 'job'), pk=pk)
    questions = analysis.questions.all()
    return render(request, 'jobs/analysis_detail.html', {'analysis': analysis, 'questions': questions})
