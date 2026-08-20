"""
Structured field extraction from raw resume text.

Uses regex + heading/section detection + keyword dictionaries. This is a
rule-based approach so the project runs with zero external NLP model
downloads. It's a reasonable baseline for real resumes and is the natural
place to plug in spaCy NER or an LLM (see services.ai_analyzer) for higher
accuracy on messy layouts.
"""
import re

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?){2,4}\d{3,4}')
YEAR_RE = re.compile(r'(19|20)\d{2}')
EXPERIENCE_YEARS_RE = re.compile(r'(\d+(?:\.\d+)?)\+?\s*years?', re.IGNORECASE)

SECTION_HEADERS = {
    'experience': ['experience', 'work experience', 'employment history', 'professional experience'],
    'education': ['education', 'academic background', 'qualifications'],
    'skills': ['skills', 'technical skills', 'core competencies', 'key skills'],
    'certifications': ['certifications', 'certificates', 'licenses'],
    'projects': ['projects', 'personal projects', 'academic projects'],
    'languages': ['languages', 'language proficiency'],
    'summary': ['summary', 'objective', 'profile', 'about me'],
}

# A broad, extensible skills dictionary. Extend freely for your domain.
SKILL_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift',
    'kotlin', 'r', 'scala', 'matlab', 'sql', 'nosql',
    'django', 'flask', 'fastapi', 'spring', 'spring boot', 'react', 'angular', 'vue', 'node.js', 'express',
    'next.js', 'html', 'css', 'sass', 'tailwind', 'bootstrap',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd', 'git', 'github', 'gitlab',
    'linux', 'nginx', 'ansible',
    'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sqlite', 'firebase',
    'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow', 'pytorch', 'keras',
    'scikit-learn', 'pandas', 'numpy', 'opencv', 'data analysis', 'data science', 'llm', 'generative ai',
    'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'jira',
    'excel', 'power bi', 'tableau', 'communication', 'leadership', 'project management', 'problem solving',
    'teamwork',
]

DEGREE_KEYWORDS = [
    'b.tech', 'be', 'b.e', 'bachelor', 'm.tech', 'me', 'm.e', 'master', 'mba', 'bca', 'mca', 'bsc', 'msc',
    'phd', 'diploma', 'associate degree',
]

LANGUAGE_KEYWORDS = [
    'english', 'hindi', 'gujarati', 'spanish', 'french', 'german', 'mandarin', 'chinese', 'japanese',
    'arabic', 'portuguese', 'russian', 'italian', 'marathi', 'tamil', 'telugu', 'bengali', 'urdu', 'punjabi',
]


def _split_sections(text: str) -> dict:
    """Very lightweight section splitter: finds lines that look like a
    section heading and groups subsequent lines under it."""
    lines = text.split('\n')
    sections = {}
    current = 'header'
    sections[current] = []

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower().strip(':').strip()
        matched_section = None
        for key, headers in SECTION_HEADERS.items():
            if lower in headers or (len(lower.split()) <= 4 and lower in headers):
                matched_section = key
                break
        if matched_section and (stripped.isupper() or len(stripped) < 40):
            current = matched_section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {k: '\n'.join(v).strip() for k, v in sections.items()}


def extract_name(text: str) -> str:
    """Heuristic: the first non-empty line that isn't an email/phone/URL and
    looks like a short "Title Case" name."""
    for line in text.split('\n')[:8]:
        stripped = line.strip()
        if not stripped:
            continue
        if EMAIL_RE.search(stripped) or 'http' in stripped.lower():
            continue
        if PHONE_RE.search(stripped) and len(stripped) < 25:
            continue
        words = stripped.split()
        if 1 <= len(words) <= 5 and all(w.replace('.', '').isalpha() for w in words):
            return stripped.title() if stripped.isupper() else stripped
    return ""


def extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    for match in PHONE_RE.finditer(text):
        candidate = match.group(0)
        digits = re.sub(r'\D', '', candidate)
        if 7 <= len(digits) <= 15:
            return candidate.strip()
    return ""


def extract_address(text: str) -> str:
    address_hint = re.search(
        r'(?:Address|Location)\s*[:\-]\s*(.+)', text, re.IGNORECASE
    )
    if address_hint:
        return address_hint.group(1).strip()[:200]
    return ""


def extract_skills(text: str) -> list:
    lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, lower):
            found.append(skill)
    # de-dup while preserving nice casing for known acronyms
    display_map = {'sql': 'SQL', 'aws': 'AWS', 'gcp': 'GCP', 'nlp': 'NLP', 'ci/cd': 'CI/CD', 'html': 'HTML',
                    'css': 'CSS', 'llm': 'LLM'}
    return [display_map.get(s, s.title()) for s in dict.fromkeys(found)]


def extract_education(sections: dict) -> list:
    block = sections.get('education', '')
    if not block:
        return []
    results = []
    for line in [l.strip() for l in block.split('\n') if l.strip()]:
        lower = line.lower()
        if any(deg in lower for deg in DEGREE_KEYWORDS):
            year_match = YEAR_RE.search(line)
            results.append({
                'degree': line,
                'year': year_match.group(0) if year_match else '',
            })
    return results


def extract_certifications(sections: dict) -> list:
    block = sections.get('certifications', '')
    if not block:
        return []
    return [l.strip('•-* \t') for l in block.split('\n') if l.strip()]


def extract_projects(sections: dict) -> list:
    block = sections.get('projects', '')
    if not block:
        return []
    return [l.strip('•-* \t') for l in block.split('\n') if l.strip()]


def extract_languages(text: str) -> list:
    lower = text.lower()
    found = [lang.capitalize() for lang in LANGUAGE_KEYWORDS if re.search(r'\b' + lang + r'\b', lower)]
    return list(dict.fromkeys(found))


def extract_experience(sections: dict) -> list:
    block = sections.get('experience', '')
    if not block:
        return []
    entries = []
    current = []
    for line in block.split('\n'):
        stripped = line.strip()
        if not stripped:
            if current:
                entries.append(' '.join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        entries.append(' '.join(current))

    parsed = []
    for entry in entries[:15]:
        years = YEAR_RE.findall(entry)
        parsed.append({'raw': entry[:300], 'years_mentioned': years})
    return parsed


def extract_total_experience_years(text: str) -> float:
    matches = EXPERIENCE_YEARS_RE.findall(text)
    if matches:
        try:
            return max(float(m) for m in matches)
        except ValueError:
            pass
    # fallback: estimate from earliest/latest years mentioned
    years = [int(y) for y in re.findall(r'\b(19[5-9]\d|20[0-4]\d)\b', text)]
    if len(years) >= 2:
        return max(0.0, float(max(years) - min(years)))
    return 0.0


def extract_all_fields(text: str) -> dict:
    """Run the full structured-extraction pipeline over raw resume text."""
    sections = _split_sections(text)
    return {
        'full_name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'address': extract_address(text),
        'skills': extract_skills(text),
        'education': extract_education(sections),
        'certifications': extract_certifications(sections),
        'experience': extract_experience(sections),
        'projects': extract_projects(sections),
        'languages': extract_languages(text),
        'total_experience_years': extract_total_experience_years(text),
    }
