
import random

import factory
from factory import fuzzy

from .models import *


Accounts = Account.objects.all()


class Factory_SolutionCategory(factory.DjangoModelFactory):

    class Meta:
        model = SolutionCategory

    @factory.lazy_attribute
    def name(self):
        return factory.Faker('text', locale='ru').generate([])[:30]

    @factory.lazy_attribute
    def description(self):
        return factory.Faker('text', locale='ru').generate([])

    @factory.lazy_attribute
    def lexer(self):
        return random.choice(CHOICES_LEXERS)[0]


class Factory_Solution(factory.DjangoModelFactory):

    class Meta:
        model = Solution

    category = fuzzy.FuzzyChoice(SolutionCategory.objects.all())
    author = fuzzy.FuzzyChoice(Account.objects.all())

    @factory.lazy_attribute
    def title(self):
        return factory.Faker('text', locale='ru').generate([])[:50]

    @factory.lazy_attribute
    def body(self):
        text_body = str()
        for i in range(3):
            text_body += factory.Faker('text', locale='ru').generate([])
        return text_body


class Factory_OpinionAboutSolution(factory.DjangoModelFactory):

    class Meta:
        model = OpinionAboutSolution

    is_useful = fuzzy.FuzzyChoice([True, False, None])

    @factory.lazy_attribute
    def is_favorite(self):
        if self.is_useful is None:
            return OpinionUserModel.CHOICES_FAVORITE.yes
        return random.choice(tuple(OpinionUserModel.CHOICES_FAVORITE._db_values))


class Factory_SolutionComment(factory.DjangoModelFactory):

    class Meta:
        model = SolutionComment

    author = fuzzy.FuzzyChoice(Accounts)
    solution = fuzzy.FuzzyChoice(Solution.objects.all())
    text_comment = factory.Faker('text', locale='ru')


class Factory_Question(factory.DjangoModelFactory):

    class Meta:
        model = Question

    author = fuzzy.FuzzyChoice(Accounts)
    text_question = factory.Faker('text', locale='ru')

    @factory.lazy_attribute
    def title(self):
        return factory.Faker('text', locale='ru').generate([])[:50] + '?'

    @factory.lazy_attribute
    def status(self):
        for i in range(200):
            random_number = random.uniform(1, 10)
            if str(random_number).endswith('1'):
                return Question.CLOSED_QUESTION
            else:
                return Question.OPEN_QUESTION


class Factory_OpinionAboutQuestion(factory.DjangoModelFactory):

    class Meta:
        model = OpinionAboutQuestion

    is_useful = fuzzy.FuzzyChoice([True, False, None])

    @factory.lazy_attribute
    def is_favorite(self):
        if self.is_useful is None:
            return OpinionUserModel.CHOICES_FAVORITE.yes
        return random.choice(tuple(OpinionUserModel.CHOICES_FAVORITE._db_values))


class Factory_Answer(factory.DjangoModelFactory):

    class Meta:
        model = Answer

    author = fuzzy.FuzzyChoice(Accounts)
    question = fuzzy.FuzzyChoice(Question.objects.all())
    text_answer = factory.Faker('text', locale='ru')

    @factory.lazy_attribute
    def is_acceptable(self):
        if self.question.has_acceptable_answer():
            return False
        return random.choice([True, False])


class Factory_OpinionAboutAnswer(factory.DjangoModelFactory):

    class Meta:
        model = OpinionAboutAnswer

    user = fuzzy.FuzzyChoice(Accounts)
    answer = fuzzy.FuzzyChoice(Answer.objects.all())
    liked_it = fuzzy.FuzzyChoice([True, False])


class Factory_AnswerComment(factory.DjangoModelFactory):

    class Meta:
        model = AnswerComment

    author = fuzzy.FuzzyChoice(Accounts)
    answer = fuzzy.FuzzyChoice(Answer.objects.all())
    text_comment = factory.Faker('text', locale='ru')


SolutionCategory.objects.filter().delete()
for i in range(10):
    category = Factory_SolutionCategory()
    # import ipdb
    # ipdb.set_trace()
    random_count_solutions = random.randrange(8)
    for j in range(random_count_solutions):
        solution = Factory_Solution(category=category)
        # generate random
        random_count_links = random.randrange(0, WebLink.MAX_COUNT_WEBLINKS_ON_OBJECT)
        random_count_tags = random.randrange(Tag.MIN_COUNT_TAGS_ON_OBJECT, Tag.MAX_COUNT_TAGS_ON_OBJECT)
        random_count_accounts = random.randrange(0, len(Accounts))
        random_count_comments = random.randrange(0, 5)
        # condition
        if random_count_links > WebLink.objects.count():
            random_count_links = WebLink.objects.count()
        if random_count_tags > Tag.objects.count():
            random_count_tags = Tag.objects.count()
        # getting objects
        web_links = random.sample(list(WebLink.objects.all()), random_count_links)
        tags = random.sample(list(Tag.objects.all()), random_count_tags)
        users = random.sample(list(Accounts), random_count_accounts)
        # setting objects
        solution.useful_links.set(web_links)
        solution.tags.set(tags)
        for user in users:
            Factory_OpinionAboutSolution(user=user, solution=solution)
        for e in range(random_count_comments):
            Factory_SolutionComment(solution=solution)

Question.objects.filter().delete()
for i in range(30):
    question = Factory_Question()
    # generate random
    random_count_tags = random.randrange(Tag.MIN_COUNT_TAGS_ON_OBJECT, Tag.MAX_COUNT_TAGS_ON_OBJECT)
    random_count_accounts = random.randrange(0, len(Accounts))
    random_count_answers = random.randrange(0, 5)
    # condition
    if random_count_tags > Tag.objects.count():
        random_count_tags = Tag.objects.count()
    # getting objects
    tags = random.sample(list(Tag.objects.all()), random_count_tags)
    users = random.sample(list(Accounts), random_count_accounts)
    # setting objects
    question.tags.set(tags)
    for user in users:
        Factory_OpinionAboutQuestion(user=user, question=question)
    for j in range(random_count_answers):
        answer = Factory_Answer(question=question)
        # generate random
        random_count_opinions = random.randrange(0, 50)
        random_count_comments = random.randrange(0, 5)
        for e in range(random_count_opinions):
            Factory_OpinionAboutAnswer(answer=answer)
        for k in range(random_count_comments):
            Factory_AnswerComment(answer=answer)