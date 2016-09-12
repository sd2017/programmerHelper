
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MinLengthValidator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.db import models
from django.conf import settings

from utils.django.models import TimeStampedModel
from utils.django.models_fields import ConfiguredAutoSlugField
from utils.django.models_utils import get_admin_url

from apps.comments.models import Comment
from apps.comments.managers import CommentManager
from apps.opinions.models import Opinion
from apps.opinions.managers import OpinionManager
from apps.flavours.models import Flavour
from apps.flavours.managers import FlavourManager
from apps.tags.models import Tag
from apps.tags.managers import TagManager

from .managers import QuestionManager, AnswerManager
from .querysets import QuestionQuerySet, AnswerQuerySet


# scrapy data question from StackOverFlow or MailList Google Groups by tags Django, JS as latest

class Question(TimeStampedModel):
    """

    """

    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    CHOICES_STATUS = (
        ('OPEN', _('Open')),
        ('CLOSED', _('Closed')),
    )

    title = models.CharField(
        _('Title'), max_length=200,
        validators=[MinLengthValidator(settings.MIN_LENGTH_FOR_NAME_OR_TITLE_OBJECT)]
    )
    slug = ConfiguredAutoSlugField(populate_from='title', unique=True)
    text_question = models.TextField(_('Text question'))
    status = models.CharField(_('Status'), max_length=50, choices=CHOICES_STATUS, default=OPEN)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('User'),
        related_name='questions', on_delete=models.CASCADE,
    )
    views = models.PositiveIntegerField(_('Views'), default=0)
    tags = models.ManyToManyField(
        Tag, related_name='questions', verbose_name=_('Tags'),
    )
    opinions = GenericRelation(Opinion, related_query_name='questions')
    flavours = GenericRelation(Flavour, related_query_name='questions')

    # managers
    objects = models.Manager()
    objects = QuestionManager.from_queryset(QuestionQuerySet)()

    opinions_manager = OpinionManager()
    tags_manager = TagManager()
    flavours_manager = FlavourManager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['-date_added']
        get_latest_by = 'date_added'

    def __str__(self):
        return _('{0.title}').format(self)

    def get_absolute_url(self):

        return reverse('questions:question', kwargs={'slug': self.slug})

    def get_admin_url(self):

        return get_admin_url(self)

    def get_count_answers(self):
        """ """

        if hasattr(self, 'count_answers'):
            return self.count_answers

        return self.answers.count()
    get_count_answers.admin_order_field = 'count_answers'
    get_count_answers.short_description = _('Count answers')

    def get_count_tags(self):
        """ """

        if hasattr(self, 'count_tags'):
            return self.count_tags

        return self.tags.count()
    get_count_tags.admin_order_field = 'count_tags'
    get_count_tags.short_description = _('Count tags')

    def get_count_opinions(self):
        """ """

        if hasattr(self, 'count_opinions'):
            return self.count_opinions

        return self.opinions.count()
    get_count_opinions.admin_order_field = 'count_opinions'
    get_count_opinions.short_description = _('Count opinions')

    def get_count_flavours(self):
        """ """

        if hasattr(self, 'count_flavours'):
            return self.count_flavours

        return self.flavours.count()
    get_count_flavours.admin_order_field = 'count_flavours'
    get_count_flavours.short_description = _('Count flavours')

    def has_accepted_answer(self):
        """ """

        if hasattr(self, 'has_accepted_answer'):
            return 1
            # return self.has_accepted_answer

        if self.answers.filter(is_accepted=True).exists():
            return True
        return False
    has_accepted_answer.short_description = _('Has accepted answer')
    has_accepted_answer.admin_order_field = 'has_accepted_answer'
    has_accepted_answer.boolean = True

    def get_rating(self):
        """ """

        if hasattr(self, 'rating'):
            return self.rating

        return self.opinions.annotate(rating=models.Case(
            models.When(is_useful=True, then=1),
            models.When(is_useful=False, then=-1),
            output_field=models.IntegerField(),
        )).aggregate(a=models.Sum('rating'))['a']
    get_rating.short_description = _('Rating')
    get_rating.admin_order_field = 'rating'

    def get_latest_activity(self):
        """ """

        return self.answers.latest().date_modified
    get_latest_activity.short_description = _('Latest activity')

    # def get_count_favorites(self):
    #     return self.opinions.filter(is_favorite=True).count()
    # get_count_favorites.short_description = _('Count favorites')

    # def get_count_unfavorites(self):
    #     return self.opinions.filter(is_favorite=False).count()
    # get_count_unfavorites.short_description = _('Count unfavorites')

    def related_questions(self):
        raise NotImplementedError
        # analysis tags


class Answer(TimeStampedModel):
    """

    """

    text_answer = models.TextField(_('Text of answer'), validators=[MinLengthValidator(20)])
    question = models.ForeignKey(
        'Question', verbose_name=_('Question'),
        on_delete=models.CASCADE, related_name='answers',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('User'),
        on_delete=models.CASCADE, related_name='answers',
    )
    is_accepted = models.BooleanField(_('Is accepted answer?'), default=False)
    comments = GenericRelation(Comment)

    objects = models.Manager()
    objects = AnswerManager()

    # comments_manager = CommentManager()

    objects = models.Manager()
    objects = AnswerManager.from_queryset(AnswerQuerySet)()

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        ordering = ['question', 'user']
        get_latest_by = 'date_modified'

    def __str__(self):
        return _('Answer on question "{0.question}" from user "{0.user}"').format(self)

    def clean(self):
        raise Exception('')
        # user may can only single answer on question
        if self.question and self.user:
            pass

    def get_rating(self):
        """ """

        count_likes = self.likes.filter(liked_it=True).count()
        count_dislikes = self.likes.filter(liked_it=False).count()
        return count_likes - count_dislikes
    get_rating.short_description = _('Mark')
    get_rating.admin_order_field = 'rating'

    def time_after_published_question(self):
        return self.date_added - self.question.date_added
