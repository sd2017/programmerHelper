
from django.db import models


class SolutionQuerySet(models.QuerySet):
    """
    QuerySet for solutions.
    """

    def solutions_with_marks(self):
        """Added for each solution new field 'mark' where storage her mark."""

        self = self.annotate(mark=models.Sum(
            models.Case(
                models.When(opinions__is_useful=True, then=1),
                models.When(opinions__is_useful=False, then=-1),
                output_field=models.IntegerField()
            )
        ))
        self = self.annotate(mark=models.functions.Coalesce('mark', 0))
        return self

    def solutions_with_count_tags(self):
        """Determinate count tags on each solution and keeping it in new field."""

        return self.annotate(count_tags=models.Count('tags', distinct=True))

    def solutions_with_count_opinions(self):
        """Determinate count opinions on each solution and keeping it in new field."""

        return self.annotate(count_opinions=models.Count('opinions', distinct=True))

    def solutions_with_count_comments(self):
        """Determinate count comments on each solution and keeping it in new field."""

        return self.annotate(count_comments=models.Count('comments', distinct=True))

    def solutions_with_all_additional_fields(self):
        """Solutions with determined: count tags, count links, count opinions, count comments, qualities, marks."""

        self = self.solutions_with_count_tags()
        self = self.solutions_with_count_opinions()
        self = self.solutions_with_count_comments()
        self = self.solutions_with_marks()
        return self
