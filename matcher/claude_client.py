import anthropic

MODEL = 'claude-sonnet-5'
MAX_INPUT_CHARS = 12000  # keeps cost/latency predictable for pathologically long input

# We ask Claude to respond by "calling" this tool instead of writing free-form
# text. Combined with tool_choice below (which forces this exact tool), this
# guarantees a parseable, schema-shaped response — much more reliable than
# asking for JSON in a prompt and hoping the model doesn't wrap it in
# markdown or add commentary around it.
ANALYSIS_TOOL = {
    'name': 'submit_analysis',
    'description': 'Submit a structured CV-to-job-posting fit analysis.',
    'input_schema': {
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
}


class ClaudeAnalysisError(Exception):
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
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[ANALYSIS_TOOL],
            tool_choice={'type': 'tool', 'name': 'submit_analysis'},
            messages=[{'role': 'user', 'content': prompt}],
        )
    except anthropic.APIError as exc:
        raise ClaudeAnalysisError(f'Claude API isteği başarısız oldu: {exc}') from exc

    tool_use = next((block for block in response.content if block.type == 'tool_use'), None)
    if tool_use is None:
        raise ClaudeAnalysisError('Claude yapılandırılmış bir yanıt döndürmedi.')

    return tool_use.input
