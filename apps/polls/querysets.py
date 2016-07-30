
from django.db import models


class PollQuerySet(models.QuerySet):
    """
    Additional methods for queryset of polls
    """

    def opened_polls(self):
        """Return only polls where status is opened"""

        return self.filter(status=self.model.CHOICES_STATUS.opened)

    def closed_polls(self):
        """Return only polls where status is closed"""

        return self.filter(status=self.model.CHOICES_STATUS.closed)

    def draft_polls(self):
        """Return only polls where status is draft"""

        return self.filter(status=self.model.CHOICES_STATUS.draft)

    def polls_with_count_votes(self):
        """Determining count a votes for each poll in a queryset."""

        return self.annotate(count_votes=models.Count('votes', distinct=True))

    def polls_with_count_choices(self):
        """Determining count a votes for each poll in a queryset."""

        return self.annotate(count_choices=models.Count('choices', distinct=True))

    def polls_with_count_choices_and_votes_and_date_lastest_voting(self):
        """Return the queryset, where each a poll has deternimed a count choices and votes itself."""

        self = self.polls_with_count_votes()
        self = self.polls_with_count_choices()
        self = self.polls_with_date_lastest_voting()
        self = self.prefetch_related('voteinpoll_set', 'choices', 'votes')
        return self

    def polls_with_date_lastest_voting(self):
        """Return a queryset with determined last voting`s date for an each polls."""

        return self.annotate(date_latest_voting=models.Max('voteinpoll__date_voting'))


class ChoiceQuerySet(models.QuerySet):
    """
    Queryset for choices
    """

    def choices_with_count_votes(self):
        """Return the queryset where each a choice have determined count a votes."""

        return self.annotate(count_votes=models.Count('votes', distinct=True))
