
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.comments.models import Comment
from apps.opinions.models import Opinion
from apps.tags.models import Tag
from utils.django.models_fields import ConfiguredAutoSlugField
from utils.django.models import TimeStampedModel

from .managers import SolutionManager
from .querysets import SolutionQuerySet


class Solution(TimeStampedModel):
    """
    Model for solution.
    """

    problem = models.CharField(
        _('Title'), max_length=100, unique=True,
        validators=[
            MinLengthValidator(settings.MIN_LENGTH_FOR_NAME_OR_TITLE_OBJECT)
        ],
        error_messages={'unique': _('Solution with this problem already exists.')}
    )
    slug = ConfiguredAutoSlugField(_('Slug'), populate_from='problem', unique=True)
    body = models.TextField(_('Text solution'), validators=[MinLengthValidator(100)])
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='solutions',
        verbose_name=_('User'),
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='solutions',
        verbose_name=_('Tags'),
    )

    comments = GenericRelation(Comment, related_query_name='solutions')
    opinions = GenericRelation(Opinion, related_query_name='solutions')

    objects = models.Manager()
    objects = SolutionManager.from_queryset(SolutionQuerySet)()

    class Meta:
        verbose_name = _("Solution")
        verbose_name_plural = _("Solutions")
        ordering = ['problem']
        get_latest_by = 'date_modified'
        permissions = (("can_view_opinions_about_solutions", "Can view opinions about solutions"),)

    def __str__(self):
        return '{0.problem}'.format(self)

    def get_absolute_url(self):
        return reverse('solutions:solution', kwargs={'pk': self.pk, 'slug': self.slug})

    def get_admin_page_url(self):
        return reverse(
            'admin:{0}_{1}_change'.format(self._meta.app_label, self._meta.model_name),
            args=(self.pk,)
        )

    def get_count_opinions(self):
        """ """
        return self.opinions.count()
    get_count_opinions.short_description = _('Count opinions')
    get_count_opinions.admin_order_field = 'count_opinions'

    def get_count_comments(self):
        """ """

        return self.comments.count()
    get_count_comments.short_description = _('Count comments')
    get_count_comments.admin_order_field = 'count_comments'

    def get_count_tags(self):
        """ """

        return self.tags.count()
    get_count_tags.short_description = _('Count tags')
    get_count_tags.admin_order_field = 'count_tags'

    def get_mark(self):
        """Getting mark of solution on based their opinions."""

        # in opinions, convert boolean to int
        self = self.opinions.annotate(is_useful_int=models.Case(
            models.When(is_useful=True, then=1),
            models.When(is_useful=False, then=-1),
            output_field=models.IntegerField()
        ))
        return self.aggregate(
            mark=models.functions.Coalesce(models.Sum('is_useful_int'), 0)
        )['mark']
    get_mark.short_description = _('Mark')
    get_mark.admin_order_field = 'mark'

    def get_critics(self):
        users = self.opinions.filter(is_useful=False).values('user')
        return get_user_model()._default_manager.filter(pk__in=users)

    def get_supporters(self):
        users = self.opinions.filter(is_useful=True).values('user')
        return get_user_model()._default_manager.filter(pk__in=users)

    def get_count_critics(self):
        return self.opinions.filter(is_useful=False).count()
    get_count_critics.short_description = _('Count critics')

    def get_count_supporters(self):
        """ """
        return self.opinions.filter(is_useful=True).count()
    get_count_supporters.short_description = _('Count supporters')

    def related_solutions(self):
        """ """

        # analysis tags
        # analysis problem
        raise NotImplementedError
