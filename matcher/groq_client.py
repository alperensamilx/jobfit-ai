import json

from groq import Groq
from groq import APIError

MODEL = 'llama-3.3-70b-versatile'
MAX_INPUT_CHARS = 12000  # keeps latency/quota usage predictable for pathologically long input

# OpenAI-style tool/function calling: instead of asking for JSON in the prompt
# and hoping the model doesn't wrap it in markdown or add commentary, we
# define a "tool" and force the model to call it (tool_choice below). The
# model's tool-call arguments are guaranteed to match this schema.
ANALYSIS_TOOL = {
    'type': 'function',
    'function': {
        'name': 'submit_analysis',
        'description': 'Submit a structured CV-to-job-posting fit analysis.',
        'parameters': {
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
        },
    },
}


class AnalysisError(Exception):
    """Raised when we can't get a usable analysis back from the API."""


def analyze_fit(cv_text, job_description):
    cv_text = cv_text[:MAX_INPUT_CHARS]
    job_description = job_description[:MAX_INPUT_CHARS]

    prompt = (
        "You are a careful, honest recruiting assistant. Compare the candidate's CV "
        "against the job posting below and call submit_analysis with your assessment. "
        "Be specific — cite actual skills/experience from the CV, and actual "
        "requirements from the posting. Don't be falsely generous with the score.\n\n"
        f"--- CV ---\n{cv_text}\n\n--- Job Posting ---\n{job_description}"
    )

    try:
        client = Groq()  # reads GROQ_API_KEY from the environment
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            tools=[ANALYSIS_TOOL],
            tool_choice={'type': 'function', 'function': {'name': 'submit_analysis'}},
        )
    except APIError as exc:
        raise AnalysisError(f'The Groq API request failed: {exc}') from exc

    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise AnalysisError('The model did not return a structured response.')

    try:
        return json.loads(tool_calls[0].function.arguments)
    except json.JSONDecodeError as exc:
        raise AnalysisError('The model response could not be parsed as structured JSON.') from exc
