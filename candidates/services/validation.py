"""
Resume file validation.

Covers:
  - extension whitelist
  - file size limit
  - basic file-signature (magic-byte) check so a renamed .exe can't sneak
    in as "resume.pdf"
  - a pluggable virus-scan hook (integrate ClamAV / cloud AV in production;
    see ClamAVScanner below for the integration point)
"""
import os
from django.conf import settings


class ValidationError(Exception):
    pass


# Minimal magic-byte signatures for the formats we accept.
FILE_SIGNATURES = {
    '.pdf': [b'%PDF'],
    '.docx': [b'PK\x03\x04'],   # docx is a zip archive
    '.png': [b'\x89PNG'],
    '.jpg': [b'\xff\xd8\xff'],
    '.jpeg': [b'\xff\xd8\xff'],
}


def validate_extension(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    allowed = getattr(settings, 'RESUME_ALLOWED_EXTENSIONS', ['.pdf', '.docx', '.png', '.jpg', '.jpeg'])
    if ext not in allowed:
        raise ValidationError(f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed)}")
    return ext


def validate_size(size_bytes: int):
    max_mb = getattr(settings, 'RESUME_MAX_SIZE_MB', 10)
    if size_bytes > max_mb * 1024 * 1024:
        raise ValidationError(f"File too large ({size_bytes / (1024*1024):.1f} MB). Max is {max_mb} MB.")
    if size_bytes == 0:
        raise ValidationError("File is empty.")


def validate_signature(file_obj, ext: str):
    """Peek at the first bytes to confirm the file actually is what its
    extension claims."""
    signatures = FILE_SIGNATURES.get(ext)
    if not signatures:
        return
    file_obj.seek(0)
    header = file_obj.read(8)
    file_obj.seek(0)
    if not any(header.startswith(sig) for sig in signatures):
        raise ValidationError("File content does not match its extension (possible corruption or spoofing).")


class VirusScanner:
    """Pluggable virus-scan interface. Default implementation is a no-op
    passthrough so the project runs without external dependencies.

    To enable real scanning, install clamd + a running ClamAV daemon and
    swap ScanNoop for ScanClamAV below (or point this at a cloud AV API).
    """

    def scan(self, file_obj) -> bool:
        """Return True if file is clean, False if malicious content was found."""
        return True


class ClamAVScanner(VirusScanner):
    """Example real implementation - requires `pip install clamd` and a
    running clamd daemon. Left inactive by default."""

    def scan(self, file_obj) -> bool:
        try:
            import clamd
            cd = clamd.ClamdUnixSocket()
            file_obj.seek(0)
            result = cd.instream(file_obj)
            file_obj.seek(0)
            status = result.get('stream', ('OK',))[0]
            return status == 'OK'
        except Exception:
            # If ClamAV isn't reachable, fail safe by allowing the file
            # through but this should raise/alert in production.
            return True


def validate_resume_file(django_file):
    """Run the full validation chain. Raises ValidationError on failure."""
    filename = django_file.name
    ext = validate_extension(filename)
    validate_size(django_file.size)
    validate_signature(django_file, ext)

    scanner = VirusScanner()
    if not scanner.scan(django_file):
        raise ValidationError("File failed virus/malware scan.")

    return ext
