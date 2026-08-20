# AI HR Management System (Django)

A resume screening + interview assistant system implementing the pipeline:

```
Upload → Validate → PDF→Image (if needed) → OpenCV Preprocessing → OCR →
NLP Field Extraction → AI Resume Analyzer → ATS Score + Skill Gap →
Job Matching Engine → Candidate Ranking → Interview Question Generator → HR Dashboard
```

## Architecture notes / substitutions from the original diagram

Two stages in the original diagram require large pretrained model downloads
that aren't practical for a portable, self-hostable project, so they were
swapped for lighter equivalents that do the same job:

| Diagram step | Used here | Why |
|---|---|---|
| LayoutParser / YOLO / Detectron2 layout detection | Regex + heading/section detection (`candidates/services/nlp_extraction.py::_split_sections`) | No multi-GB model weights to download/host; works well on standard resume formats; easy to swap in a real layout model later |
| EasyOCR / PaddleOCR | Tesseract via `pytesseract` | Lightweight, no large model downloads, widely available as a system package |
| Gemini / OpenAI GPT | Pluggable `AI_PROVIDER` setting (`openai`, `gemini`, or `none`) | Runs with **zero API keys** out of the box using a deterministic rule-based analyzer; flip a setting to use a real LLM |

Everything else (validation, PDF→image, OpenCV preprocessing, structured
field extraction, ATS scoring, JD matching, ranking, interview question
generation, dashboard) is fully implemented and working.

## Project layout

```
hr_system/
├── candidates/              # Resume upload, extraction pipeline, Candidate model
│   ├── models.py            # Candidate, Resume
│   ├── services/
│   │   ├── validation.py    # size/type/signature checks + virus-scan hook
│   │   ├── extraction.py    # PDF/DOCX text extraction, PDF→image, OpenCV preprocessing, OCR
│   │   ├── nlp_extraction.py# regex/keyword-based structured field extraction
│   │   └── pipeline.py      # orchestrates validation → extraction → NLP → Candidate
│   ├── views.py / urls.py / forms.py / admin.py
├── jobs/                    # Job descriptions, AI analysis, matching, ranking, interview Qs
│   ├── models.py            # JobDescription, Analysis, InterviewQuestion
│   ├── services/
│   │   ├── ai_analyzer.py   # pluggable OpenAI / Gemini / rule-based analyzer
│   │   ├── matching.py      # ATS scoring + JD-vs-resume matching (skills + TF-IDF + experience)
│   │   └── analyze.py       # orchestrates analyzer + matching + interview question generation
│   ├── views.py / urls.py / forms.py / admin.py
├── dashboard/                # HR dashboard (aggregate stats, top candidates, recent activity)
├── templates/                 # Bootstrap 5 templates for all of the above
└── hr_system/                 # Django project settings/urls
```

## Setup

### 1. System dependency: Tesseract OCR

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### 2. Python environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment (optional — app works without this)

```bash
cp .env.example .env
# Edit .env to set AI_PROVIDER=openai (or gemini) and add your API key
# if you want real AI-generated summaries/questions instead of the
# built-in rule-based analyzer.
```

### 4. Database + admin user

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

## Using the app

1. **Upload Resumes** (`/candidates/upload/`) — drop in PDF/DOCX/PNG/JPG
   files. Each is validated, text-extracted (with automatic OCR fallback
   for scanned resumes), and parsed into a structured Candidate profile.
2. **Job Descriptions** (`/jobs/`) — create a job with required/preferred
   skills and minimum experience.
3. On a job's detail page, click **Analyze** for a candidate (or
   **Analyze All Unranked**) to run the AI Resume Analyzer + ATS scoring +
   JD matching + interview question generation, and see the ranked
   candidate list.
4. **Dashboard** (`/`) — pipeline-wide stats, top-ranked candidates across
   all jobs, recent activity.
5. **Django Admin** (`/admin/`) — direct data access/edits.

## Extending this project

- **Real layout detection**: swap `_split_sections()` in
  `nlp_extraction.py` for a LayoutParser/Detectron2/YOLO-based detector if
  you need robust handling of complex multi-column resume designs.
- **Better OCR**: swap `ocr_image()` in `extraction.py` for EasyOCR /
  PaddleOCR / Google Vision OCR if Tesseract accuracy isn't sufficient for
  your resume mix.
- **Real virus scanning**: `candidates/services/validation.py` has a
  `ClamAVScanner` stub — install `clamd` and a running ClamAV daemon, then
  swap it in for `VirusScanner` in `validate_resume_file()`.
- **Async processing**: for high upload volume, move
  `candidates.services.pipeline.process_resume()` and
  `jobs.services.analyze.run_analysis()` behind Celery/RQ tasks instead of
  running them synchronously in the request/response cycle.
- **Better name/entity extraction**: the current extractor is
  regex/keyword-based (zero external model downloads). For higher accuracy
  on messy resumes, integrate spaCy NER or route extraction entirely
  through the LLM analyzer.

## Notes

- SQLite is used by default (zero setup). Switch `DATABASES` in
  `hr_system/settings.py` to Postgres/MySQL for production.
- `ALLOWED_HOSTS = ['*']` and `DEBUG = True` are dev/demo defaults —
  lock these down before deploying.
- Uploaded resumes are stored under `media/resumes/`.
