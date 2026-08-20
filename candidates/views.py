from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.uploadedfile import UploadedFile

from .models import Candidate, Resume
from .forms import CandidateEditForm
from .services.validation import validate_resume_file, ValidationError as FileValidationError
from .services.pipeline import process_resume, PipelineError


def upload_resumes(request):
    """Handles single or multiple resume uploads. Each file is validated,
    stored, run through the extraction pipeline, and turned into a Candidate."""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if not files:
            messages.error(request, "Please choose at least one file to upload.")
            return redirect('candidates:upload')

        created = 0
        failed = 0
        for f in files:
            try:
                validate_resume_file(f)
            except FileValidationError as e:
                messages.error(request, f"{f.name}: {e}")
                failed += 1
                continue

            resume = Resume.objects.create(
                file=f,
                original_filename=f.name,
                file_size=f.size,
                status='validated',
            )
            try:
                process_resume(resume, django_file=f)
                created += 1
            except PipelineError as e:
                messages.error(request, f"{f.name}: processing failed ({e})")
                failed += 1

        if created:
            messages.success(request, f"Successfully processed {created} resume(s).")
        if failed:
            messages.warning(request, f"{failed} file(s) failed - see messages above.")
        return redirect('candidates:list')

    return render(request, 'candidates/upload.html')


def candidate_list(request):
    candidates = Candidate.objects.order_by('-created_at')
    return render(request, 'candidates/list.html', {'candidates': candidates})


def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    resumes = candidate.resumes.order_by('-uploaded_at')
    analyses = candidate.analyses.select_related('job').order_by('-match_score')

    if request.method == 'POST':
        form = CandidateEditForm(request.POST, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Candidate details updated.")
            return redirect('candidates:detail', pk=pk)
    else:
        form = CandidateEditForm(instance=candidate)

    return render(request, 'candidates/detail.html', {
        'candidate': candidate, 'resumes': resumes, 'analyses': analyses, 'form': form,
    })
