
import random

from django.contrib.auth import get_user_model

import factory
from factory import fuzzy

from apps.comments.factories import CommentFactory
from apps.opinions.factories import OpinionFactory
from mylabour.utils import generate_text_certain_length

from .constants import CATEGORIES_OF_SOLUTIONS
from .models import *


class SolutionCategoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = SolutionCategory

    @factory.lazy_attribute
    def description(self):
        return factory.Faker('text', locale='ru').generate([])


class SolutionFactory(factory.DjangoModelFactory):

    class Meta:
        model = Solution

    category = fuzzy.FuzzyChoice(SolutionCategory.objects.all())
    account = fuzzy.FuzzyChoice(get_user_model().objects.all())

    @factory.lazy_attribute
    def title(self):
        return factory.Faker('text', locale='ru').generate([])[:50]

    @factory.lazy_attribute
    def body(self):
        length = random.randint(100, 10000)
        return generate_text_certain_length(length)

    @factory.post_generation
    def tags(self, created, extracted, **kwargs):
        count_tags = random.randint(settings.MIN_COUNT_TAGS_ON_OBJECT, settings.MAX_COUNT_TAGS_ON_OBJECT)
        tags = random.sample(tuple(Tag.objects.all()), count_tags)
        self.tags.set(tags)

    @factory.post_generation
    def links(self, created, extracted, **kwargs):
        count_links = random.randint(settings.MIN_COUNT_WEBLINKS_ON_OBJECT, settings.MAX_COUNT_WEBLINKS_ON_OBJECT)
        links = random.sample(tuple(WebLink.objects.all()), count_links)
        self.links.set(links)

    @factory.post_generation
    def comments(self, created, extracted, **kwargs):
        for i in range(random.randint(0, 3)):
            CommentFactory(content_object=self)

    @factory.post_generation
    def opinions(self, created, extracted, **kwargs):
        for i in range(random.randint(0, 5)):
            OpinionFactory(content_object=self)


def solutions_categories_factory():
    SolutionCategory.objects.filter().delete()
    random.shuffle(CATEGORIES_OF_SOLUTIONS)
    for category_name in CATEGORIES_OF_SOLUTIONS:
        SolutionCategoryFactory(name=category_name)


def solutions_factory(count_solutions):
    if not SolutionCategory.objects.count():
        solutions_categories_factory()
    for i in range(count_solutions):
        SolutionFactory()


def categories_of_solutions_and_solutions_factory(count_solutions):
    factory_solutions(count_solutions)
