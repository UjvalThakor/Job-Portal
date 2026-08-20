from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='list'),
    path('new/', views.job_create, name='create'),
    path('<int:pk>/', views.job_detail, name='detail'),
    path('<int:pk>/edit/', views.job_edit, name='edit'),
    path('<int:job_pk>/analyze/<int:candidate_pk>/', views.analyze_candidate, name='analyze_candidate'),
    path('<int:job_pk>/analyze-all/', views.analyze_all, name='analyze_all'),
    path('analysis/<int:pk>/', views.analysis_detail, name='analysis_detail'),
]
