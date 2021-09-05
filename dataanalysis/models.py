from django.db import models


class AnalysisPeriod(models.Model):
    start_commit = models.ForeignKey('contributions.Commit', on_delete=models.CASCADE,
                                     related_name="analysis_period_beginning")
    end_commit = models.ForeignKey('contributions.Commit', on_delete=models.CASCADE,
                                   related_name="analysis_period_ending", null=True)
