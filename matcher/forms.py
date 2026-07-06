from django import forms

MAX_CV_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


class AnalyzeForm(forms.Form):
    cv = forms.FileField(label='CV (PDF)', widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    job_description = forms.CharField(
        label='İş İlanı Metni',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'İş ilanının tam metnini buraya yapıştır...',
        }),
    )

    def clean_cv(self):
        cv = self.cleaned_data['cv']
        if not cv.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Lütfen sadece PDF dosyası yükle.')
        if cv.size > MAX_CV_SIZE_BYTES:
            raise forms.ValidationError('Dosya çok büyük (maksimum 5MB).')
        return cv
