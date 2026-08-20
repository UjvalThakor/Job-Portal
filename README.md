# JobsHere — AI HR Management & Next-Gen Job Portal Platform (Django + React)

A full-stack **AI-Powered Job Portal and HR Talent Matching System** built with **Django 5** and a modern **React Single Page Application (SPA)**. The platform features an intelligent resume screening pipeline, automated ATS scoring, skill-gap analysis, candidate ranking, and an interactive technical interview question generator.

---

## 🚀 Key Features & Portals

### 1. **Modern Job Portal (`JobsHere`)**
- **Indeed-Style Master-Detail Split View**: Browse job postings on the left while viewing comprehensive descriptions, required skills, and salary benchmarks on the right without page reloads.
- **Real-Time Search & Autocomplete**: Instant search by technical job titles and locations with intelligent suggestion dropdowns.
- **Smart Filter Pills**: One-click filtering by Work Mode (Remote, Hybrid, On-site), Job Type, Experience, and Industry.
- **1-Click Apply with Instant AI Match**: Candidates can apply with their profile or uploaded resume, receiving instant real-time AI match percentages and ATS scores.
- **Applications Status Tracker**: Live dashboard tracking all submitted job applications with dynamic review statuses.
- **Saved Jobs Bookmarks**: Quick bookmarking workspace to save jobs for future review.
- **Company Directory & Reviews**: Explore top tech companies, employee ratings, culture insights, and open positions.
- **IT Salary Guide**: Real-time compensation benchmarks and salary ranges across tech roles.

### 2. **AI HR Screening & Matching Pipeline**
```
Upload Resume (PDF/DOCX/Image)
  │
  ▼
[1] Validation & Signature Verification (Size, Mime-type, Magic Byte check)
  │
  ▼
[2] Text Extraction Pipeline
    ├── Digital PDF/DOCX: Native extraction via pdfplumber & python-docx
    └── Scanned/Image Resumes: PyMuPDF rasterization → OpenCV Preprocessing → Tesseract OCR
  │
  ▼
[3] NLP Structured Field Extraction (Skills, Education, Certifications, Experience, Projects, Languages)
  │
  ▼
[4] AI Resume Analyzer (Rule-Based Engine / OpenAI GPT-4o-mini / Google Gemini 1.5 Flash)
  │
  ▼
[5] ATS Scoring & Skill Gap Analysis (Matched skills, Missing skills, Strengths, Weaknesses)
  │
  ▼
[6] Multi-Factor Job Matching Engine (Skill Overlap + Scikit-Learn TF-IDF Cosine Similarity + Experience Weighting)
  │
  ▼
[7] Candidate Ranking & Tailored Interview Question Generation (Technical, Scenario-based, Cultural questions)
  │
  ▼
[8] Interactive HR Dashboard & Candidate Q&A Answer Evaluator
```

### 3. **Pluggable AI Analyzer Engine**
| AI Provider | Configuration (`.env`) | Description |
|---|---|---|
| **Built-in Rule-Based** | `AI_PROVIDER=none` | **Default.** Runs out of the box with **zero API keys and zero cost**. Deterministic NLP matching and question generation. |
| **OpenAI** | `AI_PROVIDER=openai` | Uses `gpt-4o-mini` (or custom model) with `OPENAI_API_KEY` for deep qualitative insights. |
| **Google Gemini** | `AI_PROVIDER=gemini` | Uses `gemini-1.5-flash` with `GEMINI_API_KEY` for fast multimodal resume analysis. |

---

## 📁 Project Architecture & Layout

```
AI-HR-Management-main/
├── candidates/                  # Resume parsing, candidate extraction pipeline & models
│   ├── models.py                # Candidate & Resume database models
│   ├── services/
│   │   ├── validation.py        # File validation, size limits & virus scan hooks
│   │   ├── extraction.py        # PDF/DOCX extraction, PyMuPDF, OpenCV preprocessing & OCR
│   │   ├── nlp_extraction.py    # Structured field extraction (Skills, Education, Experience)
│   │   └── pipeline.py          # End-to-end pipeline orchestrator
│   └── views.py / urls.py / forms.py / admin.py
├── jobs/                        # Job postings, AI matching, rankings & interview generation
│   ├── models.py                # JobDescription, Analysis, InterviewQuestion models
│   ├── services/
│   │   ├── ai_analyzer.py       # Pluggable AI engine (Rule-based / OpenAI / Gemini)
│   │   ├── matching.py          # ATS scoring + TF-IDF cosine matching + skill-gap calculator
│   │   └── analyze.py           # Orchestrates analysis and question generation
│   └── management/commands/
│       └── seed_demo_data.py    # Populates sample jobs, candidates, and AI evaluations
├── dashboard/                    # HR management dashboard & metrics
├── hr_system/                   # Project configuration & REST API views
│   ├── api_views.py             # REST API endpoints for React SPA frontend
│   ├── settings.py              # Django settings
│   └── urls.py                  # API routes & SPA entry point
├── static/
│   ├── css/react_styles.css     # Unified modern pill design & responsive styles
│   └── js/react_app.js          # React 18 frontend (Portal, Search, Modals, Evaluations)
├── templates/
│   └── react_index.html         # Main SPA entry template
└── manage.py
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites & Virtual Environment
Ensure you have **Python 3.10+** installed.

```bash
# Clone or navigate to the project root
cd AI-HR-Management-main

# Create virtual environment
python -m venv venv

# Activate virtual environment:
# Windows (PowerShell):
.\venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Optional: Tesseract OCR (For scanned/image-only resumes)
- **Windows**: Download and install the [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`

*(Note: Standard digital PDF and DOCX files extract text directly with zero OCR required).*

### 3. Environment Configuration (Optional)
The system runs completely offline with zero API keys by default. To enable external LLMs:
```bash
# Windows:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```
Edit `.env` and configure `AI_PROVIDER=openai` or `AI_PROVIDER=gemini` with your respective API key.

### 4. Database Setup & Seed Demo Data
```bash
# Apply database migrations
python manage.py migrate

# Seed sample jobs, candidates, and AI matching evaluations
python manage.py seed_demo_data

# Create admin superuser for Django Admin
python manage.py createsuperuser
```

### 5. Start the Application
```bash
python manage.py runserver
```

Open your browser and explore:
- 🌐 **JobsHere Portal & HR App**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- ⚙️ **Django Admin Dashboard**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🔌 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/dashboard/` | `GET` | Pipeline summary stats, top candidates, and recent activity |
| `/api/jobs/` | `GET` | List all job descriptions with applicant counts |
| `/api/jobs/create/` | `POST` | Create a new job opening |
| `/api/jobs/<id>/` | `GET` | Fetch job details and ranked matching candidates |
| `/api/jobs/<id>/apply/` | `POST` | 1-Click Apply for a candidate with real-time AI match |
| `/api/candidates/` | `GET` | List all candidate profiles and extracted skills |
| `/api/upload/` | `POST` | Upload and process resume files through extraction pipeline |
| `/api/analyze/<job_id>/<candidate_id>/` | `POST` | Run AI analyzer, ATS scoring, and interview generator |
| `/api/analysis/<id>/evaluate-answers/` | `POST` | Grade candidate answers to generated interview questions |

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Django 5.x, SQLite (Production ready for PostgreSQL/MySQL)
- **Frontend**: React 18, Babel Standalone, Vanilla Modern CSS, FontAwesome 6, Google Fonts
- **AI & NLP**: Scikit-learn (TF-IDF, Cosine Similarity), OpenCV, PyMuPDF, pdfplumber, python-docx, pytesseract
- **LLM Integrations**: OpenAI API (`gpt-4o-mini`), Google Gemini API (`gemini-1.5-flash`), Rule-based Fallback
