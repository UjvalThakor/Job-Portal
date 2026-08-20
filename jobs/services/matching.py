"""
ATS scoring + Job Matching Engine + Candidate Ranking.

- ATS score: how complete/well-structured the resume itself is (independent
  of any specific job) — presence of contact info, skills, education,
  experience, quantifiable content, length, etc.
- Match score: how well a candidate's resume fits a *specific* job
  description, combining:
    (a) required/preferred skill overlap
    (b) TF-IDF cosine similarity between resume text and JD text
    (c) experience-years fit
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_ats_score(candidate, resume_text: str) -> float:
    """Score 0-100 for resume completeness/quality, independent of any JD."""
    score = 0.0
    max_score = 100.0

    # Contact info completeness (20 pts)
    if candidate.email:
        score += 10
    if candidate.phone:
        score += 10

    # Skills present (20 pts)
    n_skills = len(candidate.skills or [])
    score += min(20, n_skills * 2)

    # Education present (15 pts)
    if candidate.education:
        score += 15

    # Experience present (20 pts)
    if candidate.experience:
        score += min(20, len(candidate.experience) * 5)

    # Certifications / projects (10 pts)
    if candidate.certifications:
        score += 5
    if candidate.projects:
        score += 5

    # Resume length / substance (15 pts) - penalize very sparse or absurdly short resumes
    length = len(resume_text or '')
    if length > 1500:
        score += 15
    elif length > 600:
        score += 10
    elif length > 200:
        score += 5

    return round(min(score, max_score), 1)


def _skill_overlap(resume_skills: list, required: list, preferred: list):
    resume_lower = {s.lower() for s in resume_skills}
    req_lower = [s.lower() for s in required]
    pref_lower = [s.lower() for s in preferred]

    matched_required = [s for s in required if s.lower() in resume_lower]
    missing_required = [s for s in required if s.lower() not in resume_lower]
    matched_preferred = [s for s in preferred if s.lower() in resume_lower]

    return matched_required, missing_required, matched_preferred


def compute_text_similarity(resume_text: str, jd_text: str) -> float:
    """TF-IDF cosine similarity between resume text and JD text, as a 0-100 score."""
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=2000)
        matrix = vectorizer.fit_transform([resume_text, jd_text])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(sim) * 100, 1)
    except ValueError:
        return 0.0


def compute_match_score(candidate, resume_text: str, job) -> dict:
    """Combine skill overlap + text similarity + experience fit into a
    single 0-100 match score for a candidate against a specific job."""
    required = job.required_skills or []
    preferred = job.preferred_skills or []

    matched_required, missing_required, matched_preferred = _skill_overlap(
        candidate.skills or [], required, preferred
    )

    skill_score = 0.0
    if required:
        skill_score = (len(matched_required) / len(required)) * 100
    elif preferred:
        skill_score = (len(matched_preferred) / len(preferred)) * 100
    else:
        skill_score = 50.0  # no explicit skill list on the JD

    bonus = 0.0
    if preferred:
        bonus = min(10, (len(matched_preferred) / len(preferred)) * 10)

    text_sim = compute_text_similarity(resume_text, job.description)

    exp_score = 100.0
    if job.min_experience_years:
        ratio = (candidate.total_experience_years or 0) / job.min_experience_years
        exp_score = round(min(100, ratio * 100), 1)

    # Weighted blend: skills matter most, then text similarity, then experience fit
    final_score = round(
        (skill_score * 0.55) + (text_sim * 0.25) + (exp_score * 0.15) + bonus, 1
    )
    final_score = max(0.0, min(100.0, final_score))

    return {
        'match_score': final_score,
        'matched_skills': matched_required + [s for s in matched_preferred if s not in matched_required],
        'missing_skills': missing_required,
        'text_similarity': text_sim,
        'experience_fit': exp_score,
    }


def rank_candidates(job) -> list:
    """Return this job's Analysis rows ordered by match_score desc."""
    return list(job.analyses.select_related('candidate').order_by('-match_score'))
