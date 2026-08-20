from django.contrib import admin
from .models import JobDescription, Analysis, InterviewQuestion


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'min_experience_years', 'created_at')
    search_fields = ('title', 'department')


class InterviewQuestionInline(admin.TabularInline):
    model = InterviewQuestion
    extra = 0


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'ats_score', 'match_score', 'analyzer_source', 'created_at')
    list_filter = ('analyzer_source', 'job')
    inlines = [InterviewQuestionInline]
