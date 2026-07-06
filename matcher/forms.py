from django import forms

MAX_CV_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


class AnalyzeForm(forms.Form):
    cv = forms.FileField(label='CV (PDF)', widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    job_description = forms.CharField(
        label='Job Posting Text',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste the full job posting text here...',
        }),
    )

    def clean_cv(self):
        cv = self.cleaned_data['cv']
        if not cv.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Please upload a PDF file only.')
        if cv.size > MAX_CV_SIZE_BYTES:
            raise forms.ValidationError('File is too large (5MB max).')
        return cv
