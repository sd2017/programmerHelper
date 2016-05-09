
from django.contrib.contenttypes.fields import GenericRelation
from django.core.urlresolvers import reverse
from django.core.validators import MinLengthValidator
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings

from model_utils.fields import StatusField, MonitorField
from model_utils import Choices
from autoslug import AutoSlugField

from apps.app_generic_models.models import UserComment_Generic, UserOpinion_Generic
from mylabour.models import TimeStampedModel
from apps.app_tags.models import Tag
from apps.app_web_links.models import WebLink


class Article(TimeStampedModel):
    """
    Model for article
    """

    MIN_COUNT_SUBSECTIONS = 1
    MAX_COUNT_SUBSECTIONS = 5

    STATUS_ARTICLE = Choices(
        ('draft', _('Draft')),
        ('published', _('Published')),
    )

    title = models.CharField(
        _('Title'), max_length=200, validators=[MinLengthValidator(settings.MIN_LENGTH_FOR_NAME_OR_TITLE_OBJECT)]
    )
    slug = AutoSlugField(populate_from='title', unique=True, always_update=True, allow_unicode=True, db_index=True)
    quotation = models.CharField(_('Quotation'), max_length=200)
    picture = models.URLField(_('Picture'), max_length=1000)
    header = models.TextField(_('Header'))
    conclusion = models.TextField(_('Conclusion'))
    status = StatusField(choices_name='STATUS_ARTICLE', verbose_name=_('Status'), default=STATUS_ARTICLE.draft)
    status_changed = MonitorField(monitor='status', verbose_name=_('Status changed'))
    views = models.IntegerField(_('Count views'), default=0, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Author'),
        related_name='articles',
        limit_choices_to={'is_active': True},
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='articles',
        verbose_name=_('Tags'),
    )
    useful_links = models.ManyToManyField(
        WebLink,
        related_name='articles',
        verbose_name=_('Useful links'),
    )
    comments = GenericRelation(UserComment_Generic)
    opinions = GenericRelation(UserOpinion_Generic)

    class Meta:
        db_table = 'articles'
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        get_latest_by = 'date_added'
        ordering = ['date_added']
        unique_together = ['author', 'title']

    def __str__(self):
        return '{0.title}'.format(self)

    def get_absolute_url(self):
        return reverse('app_articles:article', kwargs={'slug': self.slug})

    def get_scope(self):
        pass


class ArticleSubsection(TimeStampedModel):

    article = models.ForeignKey(
        'Article',
        related_name='subsections',
        on_delete=models.CASCADE,
        verbose_name=_('Article'),
    )
    title = models.CharField(
        _('Title'), max_length=200, validators=[MinLengthValidator(settings.MIN_LENGTH_FOR_NAME_OR_TITLE_OBJECT)]
    )
    slug = AutoSlugField(populate_from='title', unique=True, always_update=True, allow_unicode=True, db_index=True)
    content = models.TextField(_('Content'))

    class Meta:
        db_table = 'articles_subsections'
        verbose_name = _("Subsection article")
        verbose_name_plural = _("Subsections article")
        ordering = ['article', 'date_modified']
        unique_together = ['article', 'title']

    def __str__(self):
        return 'Subsection "{0.title}"'.format(self)