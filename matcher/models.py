from django.db import models


class Analysis(models.Model):
    cv_filename = models.CharField(max_length=255)
    cv_text = models.TextField()
    job_description = models.TextField()
    match_score = models.IntegerField()
    strengths = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.cv_filename} — {self.match_score}%'
