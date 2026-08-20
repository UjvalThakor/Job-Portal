from django.db import models
from candidates.models import Candidate, Resume


class JobDescription(models.Model):
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=255, blank=True)
    description = models.TextField(help_text="Full job description text")
    required_skills = models.JSONField(default=list, blank=True)   # ["Python", "Django", ...]
    preferred_skills = models.JSONField(default=list, blank=True)
    min_experience_years = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Analysis(models.Model):
    """Result of running a candidate's resume against a job description:
    ATS score, skill-gap analysis, and JD-match score."""

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='analyses')
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name='analyses')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)

    ats_score = models.FloatField(default=0)          # 0-100, resume quality/completeness
    match_score = models.FloatField(default=0)        # 0-100, similarity to this JD
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)   # skill gap
    summary = models.TextField(blank=True)            # AI-generated or rule-based summary
    strengths = models.JSONField(default=list, blank=True)
    concerns = models.JSONField(default=list, blank=True)

    analyzer_source = models.CharField(max_length=20, default='rule_based')  # rule_based | openai | gemini

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('candidate', 'job')
        ordering = ['-match_score']

    def __str__(self):
        return f"{self.candidate} vs {self.job} ({self.match_score:.1f}%)"


class InterviewQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('experience', 'Experience-based'),
        ('project', 'Project-based'),
    ]
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='questions')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question = models.TextField()
    sample_answer = models.TextField(blank=True)
    rationale = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.question[:80]
