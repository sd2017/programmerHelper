
import itertools
import collections

from django.db import models
# from django.utils.translation import ugettext as _
from django.contrib.auth.models import BaseUserManager

from .querysets import LevelQuerySet, UserQuerySet
# from .constants import CALCULATION_REPUTATION


CALCULATION_REPUTATION = {
    'VOTE': 1,
}


class LevelManager(models.Manager):

    pass


LevelManager = LevelManager.from_queryset(LevelQuerySet)


class UserManager(BaseUserManager):
    """
    Custom manager for custom user model
    """

    def create_user(self, email, username, password, alias):
        """Create staff user with certain attributes."""

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            alias=alias,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, alias):
        """Creating superuser with certain attributes."""

        user = self.create_user(
            email=email,
            username=username,
            password=password,
            alias=alias,
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def get_filled_users_profiles(self, queryset=None):
        """Return in percents, how many filled profiles of users information.
        If given queryset, then using its as restriction for selection."""

        result = dict()
        # if queryset is none, then using all instances of models
        if queryset is None:
            queryset = self
        # listing restrictions determinating filled profile of user
        list_restictions = (
            queryset.exclude(presents_on_stackoverflow='').values_list('pk', flat=True),
            queryset.exclude(personal_website='').values_list('pk', flat=True),
            queryset.exclude(presents_on_github='').values_list('pk', flat=True),
            queryset.exclude(presents_on_gmail='').values_list('pk', flat=True),
            queryset.filter(gender__isnull=False).values_list('pk', flat=True),
            queryset.exclude(real_name='').values_list('pk', flat=True),
        )
        # counter all suitable instances
        counter = collections.Counter(
            itertools.chain(*list_restictions)
        )
        # determinating percent filled profile of user
        for pk, value in counter.items():
            result[pk] = 100 / len(list_restictions) * value
        # return as dictioinary {instance.pk: percent}
        return result


class ActiveUserManager(models.Manager):
    """ """

    pass


UserManager = UserManager.from_queryset(UserQuerySet)
