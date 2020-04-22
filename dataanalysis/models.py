from django.db import models


class AnalysisPeriod(models.Model):
    start_commit = models.ForeignKey('contributions.Commit', on_delete=models.CASCADE, related_name="analysis_period_beginning")
    end_commit = models.ForeignKey('contributions.Commit', on_delete=models.CASCADE, related_name="analysis_period_ending", null=True)

    # def save(self, *args, **kwargs):
    #
    #     start_commit.a
    #
    #
    #     super(AnalysisPeriod, self).save(*args, **kwargs)  # Call the "real" save() method.

# FIXME: Test technical debt
class TransientModel(models.Model):
    """Inherit from this class to use django constructors and serialization but no database management"""

    def save(*args, **kwargs):
        pass  # avoid exceptions if called

    class Meta:
        abstract = True  # no table for this class
        managed = False  # no database management

# FIXME: Test technical debt
class Period(TransientModel):
    abstract = True  # no table for this class
    managed = False  # no database management

    def __init__(self, period, period_alias, period_factor):
        self._period = period
        self._period_alias = period_alias
        self._period_factor = period_factor

    def __str__(self):
        return 'Periodo: ' + str(self._period) + ", Fator: " + str(self.period_factor) + ', Legenda: ' + str(self.period_alias)

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, period):
        self._period = period

    @property
    def period_alias(self):
        return self._period_alias

    @period_alias.setter
    def period_alias(self, period_alias):
        self._period_alias = period_alias

    @property
    def period_factor(self):
        return self._period_factor

    @period_factor.setter
    def period_factor(self, period_factor):
        self._period_factor = period_factor