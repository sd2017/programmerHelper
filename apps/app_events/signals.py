
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, m2m_changed, pre_save

from apps.app_events.models import Event
from apps.app_accounts.models import Account
from apps.app_courses.models import Course
from apps.app_articles.models import Article
from apps.app_testing.models import TestingSuit
from apps.app_solutions.models import Solution
from apps.app_snippets.models import Snippet
from apps.app_polls.models import VoteInPoll
from apps.app_newsletters.models import Newsletter
from apps.app_questions.models import Question, Answer
from apps.app_forum.models import ForumTopic, ForumPost
from apps.app_generic_models.models import CommentGeneric, OpinionGeneric, LikeGeneric, ScopeGeneric

MODELS_WITH_FK_ACCOUNT = [
    Article,
    Solution,
    Snippet,
    TestingSuit,
    ForumTopic,
    ForumPost,
    CommentGeneric,
    OpinionGeneric,
    LikeGeneric,
    ScopeGeneric,
    Newsletter,
    Question,
    Answer,
]


@receiver(post_save)
def signal_created_object(sender, instance, created, **kwargs):
    """Write event in log."""
    if sender in MODELS_WITH_FK_ACCOUNT:
        if hasattr(instance, 'author'):
            account = instance.author
        elif hasattr(instance, 'user'):
            account = instance.user
        if created:
            Event.objects.create(
                account=account,
                flag=Event.CHOICES_FLAGS.adding,
                message='Created new {0} "{1}".'.format(instance._meta.verbose_name.lower(), instance),
            )
        else:
            Event.objects.create(
                account=account,
                flag=Event.CHOICES_FLAGS.updating,
                message='Updated {0} "{1}".'.format(instance._meta.verbose_name.lower(), instance),
            )


@receiver(post_delete)
def signal_deleted_object(sender, instance, **kwargs):
    """Write event in log."""
    if sender in MODELS_WITH_FK_ACCOUNT:
        if hasattr(instance, 'author'):
            account = instance.author
        elif hasattr(instance, 'user'):
            account = instance.user
        Event.objects.create(
            account=account,
            flag=Event.CHOICES_FLAGS.deleting,
            message='Deleted {0} "{1}".'.format(instance._meta.verbose_name.lower(), instance),
        )


@receiver(m2m_changed)
def signal_change_authorhip_of_course(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Write event change authorship of cource."""
    if sender is Course.authorship.through and action in ['post_remove', 'post_add']:
        if action == 'post_remove':
            flag = Event.CHOICES_FLAGS.deleting
            message = 'Deleted as author from {0} "{1}".'.format(instance._meta.verbose_name.lower(), instance)
        elif action == 'post_add':
            flag = Event.CHOICES_FLAGS.adding
            message = 'Added as author to {0} "{1}".'.format(instance._meta.verbose_name.lower(), instance)
        for pk in pk_set:
            account = model.objects.get(pk=pk)
            Event.objects.create(
                account=account,
                flag=flag,
                message=message,
            )


@receiver(post_save, sender=VoteInPoll)
def signal_account_participated_in_poll(sender, instance, **kwargs):
    """Signal, what account participated in poll."""
    Event.objects.create(
        account=instance.user,
        flag=Event.CHOICES_FLAGS.adding,
        message='Participated in {0} "{1}".'.format(instance.poll._meta.verbose_name.lower(), instance.poll),
    )


@receiver(post_delete, sender=VoteInPoll)
def signal_account_removed_from_voters_in_poll(sender, instance, **kwargs):
    """Signal, what account removed from voters in poll."""
    Event.objects.create(
        account=instance.user,
        flag=Event.CHOICES_FLAGS.deleting,
        message='Removed from voters in {0} "{1}".'.format(instance.poll._meta.verbose_name.lower(), instance.poll),
    )


CHANGE_STATUS_ACCOUNT = False


@receiver(pre_save, sender=Account)
def signal_changed_status_of_account(sender, instance, **kwargs):
    """Signal attempt change status of account: is_superuser or is_active."""
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        global CHANGE_STATUS_ACCOUNT
        if not obj.is_superuser == instance.is_superuser:
            new_status_account = 'superuser' if instance.is_superuser else 'non superuser'
            message = 'Change status account as {0}.'.format(new_status_account)
            Event.objects.create(
                account=instance,
                flag=Event.CHOICES_FLAGS.profiling,
                message=message,
            )
            CHANGE_STATUS_ACCOUNT = True
        elif not obj.is_active == instance.is_active:
            if instance.is_active:
                message = 'Now account is active.'
            else:
                message = 'Account disabled.'
            Event.objects.create(
                account=instance,
                flag=Event.CHOICES_FLAGS.profiling,
                message=message,
            )
            CHANGE_STATUS_ACCOUNT = True
        else:
            CHANGE_STATUS_ACCOUNT = False


@receiver(post_save, sender=Account)
def signal_creating_updating_of_account(sender, instance, created, **kwargs):
    """Signal creating or update account of user."""
    global CHANGE_STATUS_ACCOUNT
    if created:
        message = 'Created account'
    else:
        message = 'Update account'
    if not CHANGE_STATUS_ACCOUNT:
        Event.objects.create(
            account=instance,
            flag=Event.CHOICES_FLAGS.profiling,
            message=message,
        )
    CHANGE_STATUS_ACCOUNT = False


@receiver(post_delete, sender=Account)
def signal_deleted_account(sender, instance, **kwargs):
    """Signal creating or update account of user."""
    message = 'Delete {0} "{1.username} ({1.email})"'.format(instance._meta.verbose_name.lower(), instance)
    Event.objects.create(
        account=instance,
        flag=Event.CHOICES_FLAGS.profiling,
        message=message,
    )
