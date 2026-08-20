from django.shortcuts import render
from django.db.models import Avg, Count

from candidates.models import Candidate, Resume
from jobs.models import JobDescription, Analysis


def home(request):
    stats = {
        'total_candidates': Candidate.objects.count(),
        'total_resumes': Resume.objects.count(),
        'total_jobs': JobDescription.objects.count(),
        'total_analyses': Analysis.objects.count(),
        'avg_ats_score': Analysis.objects.aggregate(avg=Avg('ats_score'))['avg'] or 0,
        'avg_match_score': Analysis.objects.aggregate(avg=Avg('match_score'))['avg'] or 0,
        'failed_resumes': Resume.objects.filter(status='failed').count(),
        'ocr_resumes': Resume.objects.filter(ocr_used=True).count(),
    }

    top_candidates = Analysis.objects.select_related('candidate', 'job').order_by('-match_score')[:10]
    recent_jobs = JobDescription.objects.annotate(n=Count('analyses')).order_by('-created_at')[:6]
    recent_resumes = Resume.objects.order_by('-uploaded_at')[:8]

    return render(request, 'dashboard/home.html', {
        'stats': stats,
        'top_candidates': top_candidates,
        'recent_jobs': recent_jobs,
        'recent_resumes': recent_resumes,
    })
