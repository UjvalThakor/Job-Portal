from django.contrib import admin
from .models import Candidate, Resume


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'total_experience_years', 'created_at')
    search_fields = ('full_name', 'email', 'phone')


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'candidate', 'status', 'ocr_used', 'uploaded_at')
    list_filter = ('status', 'ocr_used')
