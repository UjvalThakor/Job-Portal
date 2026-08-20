"""Runs a candidate's resume against a job description end-to-end:
AI Resume Analyzer -> ATS score + skill-gap -> Job Matching Engine ->
Candidate Ranking (implicit via Analysis.match_score) -> Interview Question
Generator."""
from django.db import transaction

from .ai_analyzer import get_analyzer
from .matching import compute_ats_score, compute_match_score
from jobs.models import Analysis, InterviewQuestion


@transaction.atomic
def run_analysis(candidate, job, resume=None):
    resume_text = resume.raw_text if resume else ""

    analyzer = get_analyzer()

    ats_score = compute_ats_score(candidate, resume_text)
    match_result = compute_match_score(candidate, resume_text, job)

    ai_result = analyzer.analyze(
        resume_text=resume_text,
        jd_text=job.description,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
    )

    analysis, _ = Analysis.objects.update_or_create(
        candidate=candidate,
        job=job,
        defaults={
            'resume': resume,
            'ats_score': ats_score,
            'match_score': match_result['match_score'],
            'matched_skills': match_result['matched_skills'],
            'missing_skills': match_result['missing_skills'],
            'summary': ai_result.get('summary', ''),
            'strengths': ai_result.get('strengths', []),
            'concerns': ai_result.get('concerns', []),
            'analyzer_source': analyzer.source_name,
        },
    )

    # Regenerate interview questions for this analysis
    analysis.questions.all().delete()
    questions = analyzer.generate_interview_questions(
        resume_text=resume_text,
        jd_text=job.description,
        skills=match_result['matched_skills'] or (candidate.skills or []),
        n=6,
    )
    InterviewQuestion.objects.bulk_create([
        InterviewQuestion(
            analysis=analysis,
            category=q.get('category', 'technical'),
            question=q.get('question', ''),
            sample_answer=q.get('sample_answer', ''),
            rationale=q.get('rationale', ''),
        )
        for q in questions if q.get('question')
    ])

    return analysis
