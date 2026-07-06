import json

from google import genai
from google.genai import types
from google.genai.errors import APIError

MODEL = 'gemini-2.0-flash'  # free-tier eligible; check https://ai.google.dev/gemini-api/docs/models if this changes
MAX_INPUT_CHARS = 12000  # keeps latency/quota usage predictable for pathologically long input

# Gemini's native structured-output mode: instead of asking for JSON in the
# prompt and hoping the model doesn't add commentary/markdown around it, we
# pass a response_schema and response_mime_type so the API itself guarantees
# the output matches this shape.
RESPONSE_SCHEMA = {
    'type': 'object',
    'properties': {
        'match_score': {
            'type': 'integer',
            'description': 'Overall fit score from 0 (no fit) to 100 (ideal fit).',
        },
        'strengths': {
            'type': 'array',
            'items': {'type': 'string'},
            'description': 'Specific, concrete ways the CV matches what the job posting asks for.',
        },
        'missing_skills': {
            'type': 'array',
            'items': {'type': 'string'},
            'description': 'Requirements from the job posting not evidenced anywhere in the CV.',
        },
        'summary': {
            'type': 'string',
            'description': 'A 2-3 sentence overall assessment, written for the candidate to read.',
        },
    },
    'required': ['match_score', 'strengths', 'missing_skills', 'summary'],
}


class AnalysisError(Exception):
    """Raised when we can't get a usable analysis back from the API."""


def analyze_fit(cv_text, job_description):
    cv_text = cv_text[:MAX_INPUT_CHARS]
    job_description = job_description[:MAX_INPUT_CHARS]

    prompt = (
        "You are a careful, honest recruiting assistant. Compare the candidate's CV "
        "against the job posting below and return your assessment. "
        "Be specific — cite actual skills/experience from the CV, and actual "
        "requirements from the posting. Don't be falsely generous with the score.\n\n"
        f"--- CV ---\n{cv_text}\n\n--- Job Posting ---\n{job_description}"
    )

    try:
        client = genai.Client()  # reads GEMINI_API_KEY (or GOOGLE_API_KEY) from the environment
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=RESPONSE_SCHEMA,
            ),
        )
    except APIError as exc:
        raise AnalysisError(f'Gemini API isteği başarısız oldu: {exc}') from exc

    if not response.text:
        raise AnalysisError('Gemini boş bir yanıt döndürdü.')

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise AnalysisError('Gemini yanıtı yapılandırılmış JSON olarak ayrıştırılamadı.') from exc
