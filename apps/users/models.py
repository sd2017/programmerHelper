
import logging
import urllib
import hashlib

from django.contrib.postgres.fields import ArrayField
from django import template
from django.utils.html import format_html
# from django.template.defaultfilters import truncatechars
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models, router
from django.conf import settings
from django.core.cache import cache
# from django.contrib.auth import password_validation

from utils.django import models_fields as utils_models_fields
from utils.django.models import Viewable, Updateable, UUIDable
from utils.django.models_utils import get_admin_url

from apps.badges.managers import BadgeManager

from apps.badges.modelmixins import BadgeModelMixin
from apps.comments.modelmixins import UserCommentModelMixin
from apps.opinions.modelmixins import UserOpinionModelMixin
from apps.articles.modelmixins import ArticleModelMixin, UserMarkModelMixin
from apps.snippets.modelmixins import SnippetModelMixin
from apps.questions.modelmixins import QuestionModelMixin, AnswerModelMixin
from apps.library.modelmixins import UserReplyModelMixin
from apps.solutions.modelmixins import SolutionModelMixin
from apps.forums.modelmixins import UserForumModelMixin
from apps.polls.modelmixins import UserPollModelMixin
from apps.tags.modelmixins import UserTagModelMixin
from apps.notifications.modelmixins import UserNotificationModelMixin
from apps.visits.modelmixins import UserVisitModelMixin

from apps.polls.querysets import UserPollQuerySet
from apps.solutions.querysets import UserSolutionQuerySet
from apps.visits.querysets import UserAttendanceQuerySet
from apps.questions.querysets import UserQuestionQuerySet, UserAnswerQuerySet
from apps.articles.querysets import UserArticleQuerySet, UserMarkQuerySet
from apps.snippets.querysets import UserSnippetQuerySet
from apps.comments.querysets import UserCommentQuerySet
from apps.library.querysets import UserReplyQuerySet
from apps.opinions.querysets import UserOpinionQuerySet
from apps.forums.querysets import UserForumQuerySet
from apps.tags.querysets import UserTagQuerySet
from apps.badges.querysets import UserBadgeQuerySet
from apps.notifications.querysets import UserNotificationQuerySet

from .managers import UserManager, LevelManager
from .exceptions import ProtectDeleteUser
from .utils import UserCollector
from .validators import UsernameValidator


logger = logging.getLogger('django.development')


logger.info('Example user page https://www.digitalocean.com/community/users/jellingwood?primary_filter=upvotes_given')
logger.info('get_chart_visits')
logger.info('get_chart_activity')


class Level(models.Model):
    """

    """

    PLATINUM = 'platinum'
    GOLDEN = 'golden'
    SILVER = 'silver'
    DIAMOND = 'diamond'
    RUBY = 'ruby'
    SAPPHIRE = 'sapphire'
    MALACHITE = 'malachite'
    AMETHYST = 'amethyst'
    EMERALD = 'emerald'
    AGATE = 'agate'
    TURQUOISE = 'turquoise'
    AMBER = 'amber'
    OPAL = 'opal'
    REGULAR = 'regular'

    CHOICES_LEVEL = (
        (PLATINUM, _('Platinum')),
        (GOLDEN, _('Gold')),
        (SILVER, _('Silver')),
        (DIAMOND, _('Diamond')),
        (RUBY, _('Ruby')),
        (SAPPHIRE, _('Sapphire')),
        (MALACHITE, _('Malachite')),
        (AMETHYST, _('Amethyst')),
        (EMERALD, _('Emerald')),
        (AGATE, _('Agate')),
        (TURQUOISE, _('Turquoise')),
        (AMBER, _('Amber')),
        (OPAL, _('Opal')),
        (REGULAR, _('Regular')),
    )

    name = models.CharField(
        _('Name'), max_length=50, choices=CHOICES_LEVEL, primary_key=True,
        error_messages={'unique': _('Level with name already exists.')}
    )
    slug = utils_models_fields.ConfiguredAutoSlugField(populate_from='name', unique=True)
    description = models.TextField(
        _('Description'), validators=[MinLengthValidator(10)]
    )
    color = utils_models_fields.ColorField(
        _('Color'), max_length=50,
        help_text=_('Choice color in hex format'),
        unique=True,
        error_messages={'unique': _('Level with color already exists.')}
    )

    objects = models.Manager()
    objects = LevelManager()

    class Meta:
        verbose_name = _('Level')
        verbose_name_plural = _('Levels')
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

    def save(self, *args, **kwargs):
        super(Level, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('users:level', kwargs={'slug': self.slug})

    def get_count_users(self):
        """ """

        if hasattr(self, 'count_users'):
            return self.count_users

        return self.users.count()
    get_count_users.admin_order_field = 'count_users'
    get_count_users.short_description = _('Count users')


class User(AbstractBaseUser, PermissionsMixin, UserCommentModelMixin, UserOpinionModelMixin, ArticleModelMixin,
    SnippetModelMixin, UserMarkModelMixin, QuestionModelMixin, AnswerModelMixin, UserReplyModelMixin,
    SolutionModelMixin, UserPollModelMixin, UserForumModelMixin, UserTagModelMixin, BadgeModelMixin,
    UserNotificationModelMixin, UserVisitModelMixin, UUIDable):
    """
    Custom auth user model with additional fields and username fields as email
    """

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ('email', 'alias')

    email = models.EmailField(
        _('email'), unique=True,
        error_messages={
            'unique': _('User with this email already exists.')
        }
    )
    username = models.CharField(
        _('username'), max_length=40, unique=True,
        error_messages={
            'unique': _('User with this username already exists.')
        },
        validators=[
            MinLengthValidator(3),
            UsernameValidator(),
        ],
        help_text=UsernameValidator.help_text,
    )
    alias = models.CharField(
        _('alias'), max_length=200,
        help_text=_('Name for public display'),
    )
    is_active = models.BooleanField(_('is active?'), default=True)
    level = models.ForeignKey(
        'level',
        verbose_name='level',
        related_name='users',
        default=Level.REGULAR,
    )
    reputation = models.IntegerField(_('reputation'), default=0, editable=False)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)

    # managers
    objects = models.Manager()
    objects = UserManager()

    # external managers
    polls_manager = UserPollQuerySet.as_manager()
    visits_manager = UserAttendanceQuerySet().as_manager()
    questions_manager = UserQuestionQuerySet().as_manager()
    answers_manager = UserAnswerQuerySet().as_manager()
    articles_manager = UserArticleQuerySet().as_manager()
    solutions_manager = UserSolutionQuerySet().as_manager()
    snippets_manager = UserSnippetQuerySet().as_manager()
    comments_manager = UserCommentQuerySet().as_manager()
    replies_manager = UserReplyQuerySet().as_manager()
    opinions_manager = UserOpinionQuerySet().as_manager()
    marks_manager = UserMarkQuerySet().as_manager()
    forums_manager = UserForumQuerySet().as_manager()
    tags_manager = UserTagQuerySet().as_manager()
    badges_manager = UserBadgeQuerySet().as_manager()
    notifications_manager = UserNotificationQuerySet().as_manager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ('-date_joined', )
        get_latest_by = 'date_joined'

    def __str__(self):

        return self.get_short_name()

    def save(self, *args, **kwargs):

        super(User, self).save(*args, **kwargs)

        # autocreate profile
        self.profile

    def delete(self, using=None, keep_parents=False):

        # Protect a user from removal, if web application has this restriction
        #
        if not settings.CAN_DELETE_USER:
            raise ProtectDeleteUser(
                _(
                    """
                    Sorry, but features our the site not allow removal profile of user.
                    If you want, you can made user as non-active.
                    """
                )
            )

        using = using or router.db_for_write(self.__class__, instance=self)
        assert self._get_pk_val() is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        collector = UserCollector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()

    def get_absolute_url(self):

        return reverse('users:detail', kwargs={'email': self.email})

    def get_admin_url(self):
        """ """

        return get_admin_url(self)

    def get_full_name(self):
        """ """

        return '{0.username} ({0.email})'.format(self)
    get_full_name.short_description = Meta.verbose_name

    def get_short_name(self):

        return '{0.alias}'.format(self)
    get_short_name.short_description = _('Short name')
    # get_short_name.admin_order_field = 'alias'

    @property
    def is_staff(self):
        return self.is_superuser

    def has_permission(self, perm, obj=None):

        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        return False

    def has_module_permissions(self, label):

        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        return False

    def get_avatar_path(self, size=100, default='identicon'):
        """ """

        gravatar_url = "https://www.gravatar.com/avatar/"
        user_hash = hashlib.md5(self.email.lower().encode()).hexdigest()
        gravatar_parameters = urllib.parse.urlencode({'size': size, 'default': default, 'rating': 'g'})

        return '{}{}?{}'.format(gravatar_url, user_hash, gravatar_parameters)

    def display_avatar(self, size=100):
        """ """

        return format_html('<img src="{}" />', self.get_avatar_path(size))
    display_avatar.short_description = _('Avatar')

    def get_changes_reputation_for_last_week(self):

        raise NotImplementedError
        return

    def get_data_for_chart_reputation(self):

        raise NotImplementedError
        return


class Profile(Viewable, Updateable, UUIDable):
    """

    """

    MAN = 'MAN'
    WOMAN = 'WOMAN'
    UNKNOWN = 'UNKNOWN'

    CHOICES_GENDER = (
        (MAN, _('Man')),
        (WOMAN, _('Woman')),
        (UNKNOWN, _('Unknown'))
    )

    user = utils_models_fields.AutoOneToOneField(
        'User', on_delete=models.CASCADE, related_name='profile', verbose_name=_('User')
    )

    # public editable info
    about = models.TextField(_('About self'), default='', blank=True)
    signature = models.CharField(_('Signature'), max_length=50, default='', blank=True)
    on_gmail = utils_models_fields.FixedCharField(
        _('Presents on google services'),
        default='', blank=True, max_length=200,
        startswith='https://plus.google.com/u/0/',
    )
    on_github = utils_models_fields.FixedCharField(
        _('Presents on GitHub'),
        default='', blank=True, max_length=200,
        startswith='https://github.com/',
    )
    on_bitbucket = utils_models_fields.FixedCharField(
        _('Presents on Bitbucket'),
        default='', blank=True, max_length=200,
        startswith='https://bitbucket.org/',
    )
    on_stackoverflow = utils_models_fields.FixedCharField(
        _('Presents on stackoverflow.com'),
        default='', blank=True, max_length=200,
        startswith='https://stackoverflow.com/',
    )
    website = models.URLField(_('Personal website'), default='', blank=True)
    crafts = ArrayField(
        models.CharField(max_length=100),
        size=10, blank=True, null=True,
        verbose_name=_('Directions of development (by level)')
    )

    # private info
    job = models.CharField(
        _('job'), max_length=100, default='', blank=True,
    )
    gender = models.CharField(
        _('gender'), max_length=10, choices=CHOICES_GENDER,
        default=UNKNOWN,
    )
    date_birthday = models.DateField(
        _('date birthday'), null=True, blank=True,
        help_text=_('Only used for displaying age'))
    real_name = models.CharField(_('Real name'), max_length=200, default='', blank=True)
    phone = utils_models_fields.FixedCharField(
        _('Phone'), default='', blank=True, max_length=50,
        startswith='+',
    )

    # user preferences
    show_location = models.BooleanField(_('show location?'), default=False)
    show_email = models.BooleanField(_('show email'), default=True)

    # non-editable and hidden information
    latitude = models.FloatField(_('latitude'), editable=False, null=True)
    longitude = models.FloatField(_('longitude'), editable=False, null=True)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        return '{}'.format(self.user.get_short_name())

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    def get_admin_url(self):
        return get_admin_url(self)

    def display_location(self):

        template_ = template.Template(" {% load users_tags %}{% display_user_location user height %}")
        context_ = template.Context({
            'user': self,
            'height': 350,
        })
        return template_.render(context=context_)
    display_location.short_description = _('Location')

    def get_percentage_filling(self, with_sign=False):
        """Getting percent filled profile of user."""

        considering_fields = (
            'about',
            'signature',
            'on_gmail',
            'on_github',
            'on_stackoverflow',
            'on_bitbucket',
            'website',
            'job',
            'date_birthday',
            'real_name',
            'phone',
        )

        result = sum(int(bool(getattr(self, field))) for field in considering_fields)

        if self.gender is not self.UNKNOWN:
            result += 1

        result = result * 100 / len(considering_fields) + 1
        result = round(result, 2)

        if with_sign is True:
            return '{0}%'.format(result)
        return result
    get_percentage_filling.short_description = _('Percentage filling')
    get_percentage_filling.admin_order_field = 'percentage_filling'

    def latest_activity_from_github(self):
        pass

    def latest_activity_from_bitbucket(self):
        pass

    def latest_activity_from_gmail(self):
        pass

    def latest_activity_from_stackoverflow(self):
        pass
