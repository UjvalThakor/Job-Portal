from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('upload/', views.upload_resumes, name='upload'),
    path('', views.candidate_list, name='list'),
    path('<int:pk>/', views.candidate_detail, name='detail'),
]
