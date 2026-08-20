from django.db import models
from django.core.validators import FileExtensionValidator


class Candidate(models.Model):
    """A person derived from an uploaded resume. Fields are populated by the
    extraction pipeline (services.extraction) and may be edited by HR staff."""

    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=500, blank=True)

    skills = models.JSONField(default=list, blank=True)          # ["Python", "Django", ...]
    education = models.JSONField(default=list, blank=True)       # [{"degree":..., "institution":..., "year":...}]
    certifications = models.JSONField(default=list, blank=True)  # ["AWS Certified...", ...]
    experience = models.JSONField(default=list, blank=True)      # [{"title":..., "company":..., "duration":...}]
    projects = models.JSONField(default=list, blank=True)        # ["Project A - description", ...]
    languages = models.JSONField(default=list, blank=True)       # ["English", "Hindi"]

    total_experience_years = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or f"Candidate #{self.pk}"


class Resume(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('validated', 'Validated'),
        ('processing', 'Processing'),
        ('extracted', 'Extracted'),
        ('analyzed', 'Analyzed'),
        ('failed', 'Failed'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='resumes', null=True, blank=True)
    file = models.FileField(
        upload_to='resumes/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'png', 'jpg', 'jpeg'])],
    )
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0)  # bytes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    error_message = models.TextField(blank=True)

    raw_text = models.TextField(blank=True)        # OCR / extracted text output
    ocr_used = models.BooleanField(default=False)   # True if scanned-image OCR path was taken

    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.original_filename or self.file.name
