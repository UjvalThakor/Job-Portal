"""Ties together validation -> extraction -> NLP field extraction for a
single uploaded Resume, and creates/updates the linked Candidate record."""
import logging
from django.utils import timezone

from .extraction import extract_text
from .nlp_extraction import extract_all_fields
from .validation import validate_resume_file, ValidationError

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    pass


def process_resume(resume, django_file=None):
    """resume: candidates.models.Resume instance (already saved with a file).
    django_file: optional in-memory file object (e.g. straight from the
    upload form) to avoid re-reading from storage."""
    from .validation import validate_extension  # local import to avoid cycle at module load

    try:
        resume.status = 'processing'
        resume.save(update_fields=['status'])

        ext = '.' + resume.file.name.rsplit('.', 1)[-1].lower()

        file_obj = django_file or resume.file
        file_obj.seek(0)
        file_bytes = file_obj.read()
        file_obj.seek(0)

        result = extract_text(file_bytes, ext)

        resume.raw_text = result.text
        resume.ocr_used = result.ocr_used
        resume.status = 'extracted'
        resume.processed_at = timezone.now()
        resume.save(update_fields=['raw_text', 'ocr_used', 'status', 'processed_at'])

        fields = extract_all_fields(result.text)

        from candidates.models import Candidate
        if resume.candidate_id:
            candidate = resume.candidate
        else:
            candidate = Candidate()

        for key, value in fields.items():
            setattr(candidate, key, value)
        candidate.save()

        resume.candidate = candidate
        resume.save(update_fields=['candidate'])

        return candidate

    except ValidationError:
        raise
    except Exception as e:
        logger.exception("Resume processing failed for resume #%s", resume.pk)
        resume.status = 'failed'
        resume.error_message = str(e)
        resume.save(update_fields=['status', 'error_message'])
        raise PipelineError(str(e)) from e
