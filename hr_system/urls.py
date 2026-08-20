from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render
from . import api_views

def react_spa_view(request):
    return render(request, 'react_index.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # React Single Page App Main Entry
    path('', react_spa_view, name='app_home'),
    
    # Agent status endpoint (handles IDE/browser extension polling)
    path('api/agent/status/', lambda request: JsonResponse({'status': 'idle', 'agent_running': False})),
    
    # REST API endpoints
    path('api/dashboard/', api_views.api_dashboard, name='api_dashboard'),
    path('api/jobs/', api_views.api_jobs_list, name='api_jobs_list'),
    path('api/jobs/create/', api_views.api_job_create, name='api_job_create'),
    path('api/jobs/<int:pk>/', api_views.api_job_detail, name='api_job_detail'),
    path('api/jobs/<int:job_pk>/apply/', api_views.api_job_apply, name='api_job_apply'),
    path('api/candidates/', api_views.api_candidates_list, name='api_candidates_list'),
    path('api/candidates/<int:pk>/', api_views.api_candidate_detail, name='api_candidate_detail'),
    path('api/candidates/edit/<int:pk>/', api_views.api_candidate_edit, name='api_candidate_edit'),
    path('api/upload/', api_views.api_upload_resumes, name='api_upload_resumes'),
    path('api/analyze/<int:job_pk>/<int:candidate_pk>/', api_views.api_analyze_candidate, name='api_analyze_candidate'),
    path('api/analyze-all/<int:job_pk>/', api_views.api_analyze_all, name='api_analyze_all'),
    path('api/analysis/<int:pk>/', api_views.api_analysis_detail, name='api_analysis_detail'),
    path('api/analysis/<int:analysis_pk>/evaluate-answers/', api_views.api_evaluate_answers, name='api_evaluate_answers'),

    # Existing Django Template Fallbacks
    path('classic-dashboard/', include('dashboard.urls')),
    path('candidates/', include('candidates.urls')),
    path('jobs/', include('jobs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
