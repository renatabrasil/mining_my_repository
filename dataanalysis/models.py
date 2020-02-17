from django.db import models

# Create your models here.


class AnalysisPeriod(models.Model):
    start_commit = models.ForeignKey('contributions.Commit', on_delete=models.CASCADE, related_name="analysis_period_beginning")
    end_commit = models.ForeignKey('contributions.Commit', on_delete=models.CASCADE, related_name="analysis_period_ending", null=True)

    # def save(self, *args, **kwargs):
    #
    #     start_commit.a
    #
    #
    #     super(AnalysisPeriod, self).save(*args, **kwargs)  # Call the "real" save() method.
