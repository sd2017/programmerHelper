
from django.db import models

from mylabour.utils import get_random_objects
from apps.testing.models import TestingPassage


class AccountQuerySet(models.QuerySet):
    """
    Queryset for accounts.
    """

    def active_accounts(self):
        """Filter only active account."""

        return self.filter(is_active=True)

    def non_active_accounts(self):
        """Filter only non active account."""

        return self.filter(is_active=False)

    def accounts_with_total_scope_for_solutions(self, queryset=None):
        """Created new field 'total_scope_for_solutions' by help annotation and
         return new queryset for certain instance/instances or all instances, if queryset is none."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(
            total_scope_for_solutions=models.Sum(
                models.Case(
                    models.When(solutions__opinions__is_useful=True, then=1),
                    models.When(solutions__opinions__is_useful=False, then=-1),
                    output_field=models.IntegerField()
                )
            )
        )

    def accounts_with_total_scope_for_questions(self, queryset=None):
        """Created new field 'total_scope_for_questions' by help annotation and
         return new queryset for certain instance/instances or all instances, if queryset is none."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(
            total_scope_for_questions=models.Sum(
                models.Case(
                    models.When(questions__opinions__is_useful=True, then=1),
                    models.When(questions__opinions__is_useful=False, then=-1),
                    output_field=models.IntegerField()
                )
            )
        )

    def accounts_with_total_scope_for_answers(self, queryset=None):
        """Created new field 'total_scope_for_answers' by help annotation and
         return new queryset for certain instance/instances or all instances, if queryset is none."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(
            total_scope_for_answers=models.Sum(
                models.Case(
                    models.When(answers__likes__liked_it=True, then=1),
                    models.When(answers__likes__liked_it=False, then=-1),
                    output_field=models.IntegerField()
                )
            )
        )

    def accounts_with_total_scope_for_snippets(self, queryset=None):
        """Created new field 'total_scope_for_snippets' by help annotation and
         return new queryset for certain instance/instances or all instances, if queryset is none."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(
            total_scope_for_snippets=models.Sum(
                models.Case(
                    models.When(snippets__opinions__is_useful=True, then=1),
                    models.When(snippets__opinions__is_useful=False, then=-1),
                    output_field=models.IntegerField()
                )
            )
        )

    # def accounts_with_total_rating_for_articles(self, queryset=None):
    #     """Created new field 'total_rating_for_articles' by help annotation and
    #      return new queryset for certain instance/instances or all instances, if queryset is none."""
    #     # if queryset is none, then using all instances of model
    #     if queryset is None:
    #         queryset = self
    #     return Article.objects.articles_with_rating().filter(author=self).aggregate(
    #         total_rating_for_articles=models.Sum('rating')
    #     )['total_rating_for_articles']
    #     return queryset.annotate(rating=models.Avg('articles__scopes__scope'))

    def objects_with_count_opinions(self, queryset=None):
        """Annotation for getting count opinions on based queryset or all instances."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(count_opinions=models.Count('opinions', distinct=True))

    def objects_with_count_comments(self, queryset=None):
        """Annotation for getting count comments on based queryset or all instances."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(count_opinions=models.Count('comments', distinct=True))

    def objects_with_count_likes(self, queryset=None):
        """Annotation for getting count likes on based queryset or all instances."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(count_opinions=models.Count('likes', distinct=True))

    def objects_with_count_scopes(self, queryset=None):
        """Annotation for getting count scopes on based queryset or all instances."""
        # if queryset is none, then using all instances of model
        if queryset is None:
            queryset = self
        return queryset.annotate(count_opinions=models.Count('scopes', distinct=True))

    def random_accounts(self, count=1):
        """Getting certain count random objects from queryset."""

        return get_random_objects(queryset=self, count=count)

    def objects_with_count_favorites_and_unfavorites(self, queryset=None):
        """Getting count favorites and unfavorites of accounts."""
        return self.annotate(
            count_favorites=models.Sum(
                models.Case(
                    models.When(opinions__is_favorite=True, then=1),
                    output_field=models.IntegerField()
                ),
            ),
            count_unfavorites=models.Sum(
                models.Case(
                    models.When(opinions__is_favorite=False, then=1),
                    output_field=models.IntegerField()
                ),
            )
        )

    def objects_with_count_articles(self, queryset=None):
        """Getting count articles of accounts."""
        return self.annotate(count_articles=models.Count('articles', distinct=True))

    def objects_passages_testsuits(self, queryset=None):
        """Getting accounts what passed at least 1 testing suit."""
        return self.filter(passages__status=TestingPassage.CHOICES_STATUS.passed)

    def creators_testing_suits(self):
        """Getting accounts what passed at least 1 testing suit."""
        return self.filter(testing_suits__isnull=False)

    def objects_with_badge(self, badge_name):
        result = self.filter()
        for obj in self.iterator():
            if not obj.has_badge(badge_name):
                result = result.exclude(pk=obj.pk)
        return result