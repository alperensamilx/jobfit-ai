from django.shortcuts import get_object_or_404, redirect, render

from .claude_client import ClaudeAnalysisError, analyze_fit
from .forms import AnalyzeForm
from .models import Analysis
from .pdf_utils import PDFExtractionError, extract_text


def analyze_view(request):
    if request.method == 'POST':
        form = AnalyzeForm(request.POST, request.FILES)
        if form.is_valid():
            cv_file = form.cleaned_data['cv']
            job_description = form.cleaned_data['job_description']

            try:
                cv_text = extract_text(cv_file)
            except PDFExtractionError as exc:
                form.add_error('cv', str(exc))
                return render(request, 'matcher/analyze.html', {'form': form})

            try:
                result = analyze_fit(cv_text, job_description)
            except ClaudeAnalysisError as exc:
                form.add_error(None, str(exc))
                return render(request, 'matcher/analyze.html', {'form': form})

            analysis = Analysis.objects.create(
                cv_filename=cv_file.name,
                cv_text=cv_text,
                job_description=job_description,
                match_score=max(0, min(100, int(result['match_score']))),
                strengths=result['strengths'],
                missing_skills=result['missing_skills'],
                summary=result['summary'],
            )
            return redirect('matcher:result', pk=analysis.pk)
    else:
        form = AnalyzeForm()

    return render(request, 'matcher/analyze.html', {'form': form})


def result_view(request, pk):
    analysis = get_object_or_404(Analysis, pk=pk)
    return render(request, 'matcher/result.html', {'analysis': analysis})


def history_view(request):
    analyses = Analysis.objects.all()
    return render(request, 'matcher/history.html', {'analyses': analyses})
