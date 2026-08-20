"""
AI Resume Analyzer.

Pluggable across OpenAI / Gemini, controlled by settings.AI_PROVIDER.
If no API key is configured, falls back to a deterministic rule-based
analyzer so the whole pipeline runs end-to-end with zero external calls
(good for local dev/demo, and keeps this project runnable without secrets).

Usage:
    analyzer = get_analyzer()
    result = analyzer.analyze(resume_text, jd_text, required_skills, preferred_skills)
    # result = {"summary": str, "strengths": [...], "concerns": [...]}
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseAnalyzer:
    source_name = 'rule_based'

    def analyze(self, resume_text: str, jd_text: str, required_skills: list, preferred_skills: list) -> dict:
        raise NotImplementedError

    def generate_interview_questions(self, resume_text: str, jd_text: str, skills: list, n: int = 6) -> list:
        raise NotImplementedError


class RuleBasedAnalyzer(BaseAnalyzer):
    """No external calls. Deterministic, good default / offline fallback."""
    source_name = 'rule_based'

    def analyze(self, resume_text, jd_text, required_skills, preferred_skills):
        resume_lower = resume_text.lower()
        matched_required = [s for s in required_skills if s.lower() in resume_lower]
        missing_required = [s for s in required_skills if s.lower() not in resume_lower]
        matched_preferred = [s for s in preferred_skills if s.lower() in resume_lower]

        strengths = []
        if matched_required:
            strengths.append(f"Demonstrates {len(matched_required)}/{len(required_skills) or 1} required skills: "
                              f"{', '.join(matched_required[:6])}.")
        if matched_preferred:
            strengths.append(f"Also shows preferred skills: {', '.join(matched_preferred[:5])}.")

        concerns = []
        if missing_required:
            concerns.append(f"Missing required skills: {', '.join(missing_required[:6])}.")
        if len(resume_text) < 300:
            concerns.append("Resume content is quite sparse; verify details manually.")

        summary = (
            f"Candidate matches {len(matched_required)} of {len(required_skills) or 0} required skills"
            f"{' and ' + str(len(matched_preferred)) + ' preferred skills' if preferred_skills else ''}. "
            f"{'Strong alignment with role requirements.' if not missing_required else 'Some required skills appear to be missing from the resume.'}"
        )

        return {'summary': summary, 'strengths': strengths, 'concerns': concerns}

    def generate_interview_questions(self, resume_text, jd_text, skills, n=6):
        templates = [
            ("technical", "Can you walk me through a production project where you used {skill}? What technical challenges did you face?",
             "Sample Ideal Answer Key: The candidate should outline practical hands-on experience using {skill}, detailing specific architecture choices, error handling, performance benchmarks (e.g. latency, throughput), and concrete lessons learned during implementation."),

            ("technical", "How would you explain {skill} to someone unfamiliar with it, and when would you choose it over alternative solutions?",
             "Sample Ideal Answer Key: Look for clear conceptual understanding of {skill}, comparison against alternative frameworks/libraries, evaluation of trade-offs (complexity vs performance), and ideal production use cases."),

            ("experience", "Tell me about a time your technical proficiency with {skill} directly impacted a critical project outcome.",
             "Sample Ideal Answer Key: Candidate uses the STAR methodology (Situation, Task, Action, Result) to demonstrate ownership, problem-solving under pressure, and measurable metrics achieved with {skill}."),

            ("behavioral", "Describe a challenging technical disagreement or bug in a past project and how you resolved it.",
             "Sample Ideal Answer Key: Demonstrates emotional intelligence, constructive peer review, data-driven decision making, post-mortem root cause analysis, and collaborative team communication."),

            ("behavioral", "How do you maintain high code quality and test coverage when delivering features under tight sprint deadlines?",
             "Sample Ideal Answer Key: Effective task prioritization, automated CI/CD pipelines, Test-Driven Development (TDD), modular clean architecture, and active communication with product managers."),

            ("project", "Pick a major project from your resume and describe your specific design pattern choices and system impact.",
             "Sample Ideal Answer Key: Demonstrates end-to-end component lifecycle ownership, database query optimizations, API design patterns, security standards, and measurable user/business impact."),
        ]
        questions = []
        skill_cycle = skills[:max(1, n)] or ['your core technical stack']
        si = 0
        for category, template, answer_template in templates[:n]:
            skill = skill_cycle[si % len(skill_cycle)]
            si += 1
            questions.append({
                'category': category,
                'question': template.format(skill=skill),
                'sample_answer': answer_template.format(skill=skill),
                'rationale': f"Probes depth of experience with {skill}." if '{skill}' in template else "Assesses soft skills and problem solving.",
            })
        return questions[:n]


class OpenAIAnalyzer(BaseAnalyzer):
    source_name = 'openai'

    def _call(self, prompt: str) -> str:
        import requests
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def analyze(self, resume_text, jd_text, required_skills, preferred_skills):
        prompt = f"""You are an ATS resume analyzer. Given the resume and job description below,
return ONLY valid JSON (no markdown fences) with keys: summary (string), strengths (list of strings),
concerns (list of strings).

JOB DESCRIPTION:
{jd_text[:3000]}

REQUIRED SKILLS: {', '.join(required_skills)}
PREFERRED SKILLS: {', '.join(preferred_skills)}

RESUME:
{resume_text[:6000]}
"""
        try:
            raw = self._call(prompt)
            return json.loads(raw.strip().strip('```json').strip('```'))
        except Exception as e:
            logger.warning("OpenAI analyze failed, falling back to rule-based: %s", e)
            return RuleBasedAnalyzer().analyze(resume_text, jd_text, required_skills, preferred_skills)

    def generate_interview_questions(self, resume_text, jd_text, skills, n=6):
        prompt = f"""Generate {n} interview questions for a candidate based on their resume and this job description.
Return ONLY valid JSON: a list of objects with keys category (technical|behavioral|experience|project),
question (string), sample_answer (string - expected ideal answer points), rationale (short string).

JOB DESCRIPTION:
{jd_text[:2000]}

RESUME:
{resume_text[:4000]}
"""
        try:
            raw = self._call(prompt)
            return json.loads(raw.strip().strip('```json').strip('```'))
        except Exception as e:
            logger.warning("OpenAI question-gen failed, falling back to rule-based: %s", e)
            return RuleBasedAnalyzer().generate_interview_questions(resume_text, jd_text, skills, n)


class GeminiAnalyzer(BaseAnalyzer):
    source_name = 'gemini'

    def _call(self, prompt: str) -> str:
        import requests
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}")
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    def analyze(self, resume_text, jd_text, required_skills, preferred_skills):
        prompt = f"""Return ONLY valid JSON (no markdown) with keys summary, strengths (list), concerns (list),
analyzing this resume against the job description.

JOB DESCRIPTION:
{jd_text[:3000]}
REQUIRED SKILLS: {', '.join(required_skills)}
PREFERRED SKILLS: {', '.join(preferred_skills)}
RESUME:
{resume_text[:6000]}
"""
        try:
            raw = self._call(prompt)
            return json.loads(raw.strip().strip('```json').strip('```'))
        except Exception as e:
            logger.warning("Gemini analyze failed, falling back to rule-based: %s", e)
            return RuleBasedAnalyzer().analyze(resume_text, jd_text, required_skills, preferred_skills)

    def generate_interview_questions(self, resume_text, jd_text, skills, n=6):
        prompt = f"""Generate {n} interview questions as ONLY valid JSON: a list of objects with keys
category (technical|behavioral|experience|project), question, sample_answer, rationale.
JOB DESCRIPTION:
{jd_text[:2000]}
RESUME:
{resume_text[:4000]}
"""
        try:
            raw = self._call(prompt)
            return json.loads(raw.strip().strip('```json').strip('```'))
        except Exception as e:
            logger.warning("Gemini question-gen failed, falling back to rule-based: %s", e)
            return RuleBasedAnalyzer().generate_interview_questions(resume_text, jd_text, skills, n)


def get_analyzer() -> BaseAnalyzer:
    provider = getattr(settings, 'AI_PROVIDER', 'none')
    if provider == 'openai' and getattr(settings, 'OPENAI_API_KEY', ''):
        return OpenAIAnalyzer()
    if provider == 'gemini' and getattr(settings, 'GEMINI_API_KEY', ''):
        return GeminiAnalyzer()
    return RuleBasedAnalyzer()
