from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .claude_client import ClaudeAnalysisError
from .models import Analysis
from .pdf_utils import PDFExtractionError, extract_text

FIXTURE_PDF = Path(__file__).parent / 'test_fixtures' / 'sample_cv.pdf'

FAKE_CLAUDE_RESULT = {
    'match_score': 82,
    'strengths': ['4 years of backend experience', 'Django and PostgreSQL match the stack'],
    'missing_skills': ['No mention of Kubernetes'],
    'summary': 'Strong overall fit for a backend role.',
}


def make_cv_upload():
    return SimpleUploadedFile('sample_cv.pdf', FIXTURE_PDF.read_bytes(), content_type='application/pdf')


class PDFExtractionTests(TestCase):
    def test_extracts_text_from_valid_pdf(self):
        text = extract_text(make_cv_upload())
        self.assertIn('Jane Doe', text)
        self.assertIn('Python', text)

    def test_raises_on_unreadable_file(self):
        garbage = SimpleUploadedFile('fake.pdf', b'this is not a pdf', content_type='application/pdf')
        with self.assertRaises(PDFExtractionError):
            extract_text(garbage)


class AnalyzeFormValidationTests(TestCase):
    def test_non_pdf_extension_is_rejected(self):
        file = SimpleUploadedFile('cv.txt', b'hello', content_type='text/plain')
        response = self.client.post(reverse('matcher:analyze'), {
            'cv': file, 'job_description': 'Some job posting text.',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PDF')
        self.assertEqual(Analysis.objects.count(), 0)


class AnalyzeViewTests(TestCase):
    def test_get_renders_upload_form(self):
        response = self.client.get(reverse('matcher:analyze'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CV')

    @patch('matcher.views.analyze_fit')
    def test_successful_analysis_creates_record_and_redirects(self, mock_analyze_fit):
        mock_analyze_fit.return_value = FAKE_CLAUDE_RESULT

        response = self.client.post(reverse('matcher:analyze'), {
            'cv': make_cv_upload(), 'job_description': 'We need a backend engineer with Django experience.',
        })

        self.assertEqual(Analysis.objects.count(), 1)
        analysis = Analysis.objects.first()
        self.assertEqual(analysis.match_score, 82)
        self.assertEqual(analysis.strengths, FAKE_CLAUDE_RESULT['strengths'])
        self.assertEqual(analysis.missing_skills, FAKE_CLAUDE_RESULT['missing_skills'])
        self.assertIn('Jane Doe', analysis.cv_text)
        self.assertRedirects(response, reverse('matcher:result', args=[analysis.pk]))

        mock_analyze_fit.assert_called_once()

    @patch('matcher.views.analyze_fit')
    def test_claude_error_shows_message_without_saving(self, mock_analyze_fit):
        mock_analyze_fit.side_effect = ClaudeAnalysisError('API is down')

        response = self.client.post(reverse('matcher:analyze'), {
            'cv': make_cv_upload(), 'job_description': 'Some job posting.',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'API is down')
        self.assertEqual(Analysis.objects.count(), 0)

    def test_score_is_clamped_to_0_100(self):
        with patch('matcher.views.analyze_fit') as mock_analyze_fit:
            mock_analyze_fit.return_value = {**FAKE_CLAUDE_RESULT, 'match_score': 150}
            self.client.post(reverse('matcher:analyze'), {
                'cv': make_cv_upload(), 'job_description': 'Some job posting.',
            })
        self.assertEqual(Analysis.objects.first().match_score, 100)


class ResultAndHistoryViewTests(TestCase):
    def setUp(self):
        self.analysis = Analysis.objects.create(
            cv_filename='sample_cv.pdf',
            cv_text='Jane Doe, Python, Django',
            job_description='Backend engineer wanted.',
            match_score=82,
            strengths=FAKE_CLAUDE_RESULT['strengths'],
            missing_skills=FAKE_CLAUDE_RESULT['missing_skills'],
            summary=FAKE_CLAUDE_RESULT['summary'],
        )

    def test_result_view_shows_score_and_details(self):
        response = self.client.get(reverse('matcher:result', args=[self.analysis.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '82')
        self.assertContains(response, 'Kubernetes')

    def test_history_view_lists_past_analyses(self):
        response = self.client.get(reverse('matcher:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'sample_cv.pdf')
