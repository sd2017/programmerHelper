
from unittest import mock

from django.forms import widgets
from django.utils.text import force_text
from django.apps import apps
from django.core.management import call_command

import magic
import pytest

from utils.django.test_utils import EnhancedTestCase
from config.admin import AdminSite

from apps.polls.admin import PollAdmin, ChoiceAdmin, VoteAdmin, ChoiceInline, VoteInline
from apps.polls.models import Poll, Choice, Vote
from apps.polls.factories import PollFactory, ChoiceFactory


class PollsAdminTests(EnhancedTestCase):

    @classmethod
    def setUpTestData(cls):

        call_command('factory_test_users', '1')

        cls.active_superuser = cls.django_user_model.objects.get()
        cls._make_user_as_active_superuser(cls.active_superuser)

    def test_app_index_page(self):
        url = self.reverse('admin:app_list', kwargs={'app_label': 'polls'})
        self.client.force_login(self.active_superuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('polls/admin/app_index.html')


class PollAdminTests(EnhancedTestCase):
    """
    Tests for admin view of polls
    """

    @classmethod
    def setUpTestData(cls):

        call_command('factory_test_users', '3')

        cls.poll1 = PollFactory(status='opened')
        cls.poll2 = PollFactory(status='draft')
        cls.poll3 = PollFactory(status='closed')

        cls.active_superuser, cls.user2, cls.user3 = cls.django_user_model.objects.all()
        cls._make_user_as_active_superuser(cls.active_superuser)

        url = cls.reverse('admin:polls_statistics')
        cls.request_for_view_statistics = cls.factory.get(url)
        cls.request_for_view_statistics.user = cls.active_superuser

        cls.url_polls_make_report = cls.reverse('admin:polls_make_report')

        cls.PollAdmin = PollAdmin(Poll, AdminSite)

    def setUp(self):
        self.client.force_login(self.active_superuser)

        self.choice11 = ChoiceFactory(poll=self.poll1)
        self.choice21 = ChoiceFactory(poll=self.poll2)
        self.choice31 = ChoiceFactory(poll=self.poll3)

    def test_get_queryset_must_return_objects_with_annotated_fields(self):

        qs = self.PollAdmin.get_queryset(self.mockrequest)

        values_poll = qs.values()[0]
        self.assertIn('count_votes', values_poll)
        self.assertIn('count_choices', values_poll)
        self.assertIn('date_latest_voting', values_poll)

    def test_get_inline_instances_if_poll_does_not_exists(self):

        inlines = self.PollAdmin.get_inline_instances(self.mockrequest)
        self.assertEqual(len(inlines), 1)
        self.assertIsInstance(inlines[0], ChoiceInline)

    def test_get_inline_instances_if_poll_has_no_votes(self):

        inlines = self.PollAdmin.get_inline_instances(self.mockrequest, self.poll1)
        self.assertEqual(len(inlines), 1)
        self.assertIsInstance(inlines[0], ChoiceInline)

    def test_get_inline_instances_if_poll_has_1_vote(self):

        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)

        inlines = self.PollAdmin.get_inline_instances(self.mockrequest, self.poll1)
        self.assertEqual(len(inlines), 2)
        self.assertIsInstance(inlines[0], ChoiceInline)
        self.assertIsInstance(inlines[1], VoteInline)

    def test_change_view_if_poll_has_no_votes_and_test_used_template(self):

        response = self.client.get(self.poll1.get_admin_url())

        self.assertTemplateUsed(response, 'polls/admin/poll_change_form.html')

        self.assertNotIn('chart_poll_result', response.context_data.keys())

    def test_change_view_if_poll_has_votes_and_test_used_template(self):

        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)

        response = self.client.get(self.poll1.get_admin_url())

        self.assertTemplateUsed(response, 'polls/admin/poll_change_form.html')

        self.assertIn('chart_poll_result', response.context_data.keys())
        svg_chart = response.context_data['chart_poll_result']
        self.assertEqual(magic.from_buffer(svg_chart, mime=True), 'application/xml')

    def test_get_fieldsets_if_poll_does_not_exists(self):

        fieldsets = self.PollAdmin.get_fieldsets(self.mockrequest)
        fields = ['title', 'slug', 'status']
        self.assertListEqual(fieldsets, [[Poll._meta.verbose_name, {'fields': fields}]])

    def test_get_fieldsets_if_poll_has_not_votes(self):

        fieldsets = self.PollAdmin.get_fieldsets(self.mockrequest, self.poll1)
        fields = ['title', 'slug', 'status', 'status_changed', 'get_count_votes', 'get_count_choices']
        self.assertListEqual(fieldsets, [[Poll._meta.verbose_name, {'fields': fields}]])

    def test_get_fieldsets_if_poll_has_votes(self):

        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)

        fieldsets = self.PollAdmin.get_fieldsets(self.mockrequest, self.poll1)
        fields = [
            'title', 'slug', 'status', 'status_changed', 'get_count_votes', 'get_count_choices',
            'get_date_lastest_voting', 'get_most_popular_choice_or_choices_as_html'
        ]
        self.assertListEqual(fieldsets, [[Poll._meta.verbose_name, {'fields': fields}]])

    def test_get_urls(self):

        urls = self.PollAdmin.get_urls()
        urls_names = (url.name for url in urls)

        self.assertIn('polls_poll_preview', urls_names)
        self.assertIn('polls_make_report', urls_names)
        self.assertIn('polls_statistics', urls_names)

    @pytest.mark.xfail(reason='Not implemented Preview for poll in Admin')
    def test_accessibility_urls(self):

        urls = self.PollAdmin.get_urls()

        for url in urls:
            if url.name == 'polls_poll_changelist':
                urlpath = self.reverse('admin:polls_poll_changelist')
                response = self.client.get(urlpath)
                self.assertEqual(response.status_code, 200)
            elif url.name == 'polls_poll_change':
                urlpath = self.reverse('admin:polls_poll_change', args=[self.poll1.pk])
                response = self.client.get(urlpath)
                self.assertEqual(response.status_code, 200)
            elif url.name == 'polls_poll_history':
                urlpath = self.reverse('admin:polls_poll_history', args=[self.poll1.pk])
                response = self.client.get(urlpath)
                self.assertEqual(response.status_code, 200)
            elif url.name == 'polls_poll_delete':
                urlpath = self.reverse('admin:polls_poll_delete', args=[self.poll1.pk])
                response = self.client.get(urlpath)
                self.assertEqual(response.status_code, 200)
            # elif url.name == 'polls_poll_preview':
            #     urlpath = self.reverse('admin:polls_poll_preview', args=[self.poll1.pk])
            elif url.name == 'polls_make_report':
                urlpath = self.reverse('admin:polls_make_report')
                response = self.client.get(urlpath)
                self.assertEqual(response.status_code, 200)
            elif url.name == 'polls_statistics':
                urlpath = self.reverse('admin:polls_statistics')
                response = self.client.get(urlpath)
                self.assertEqual(response.status_code, 200)

    def test_get_listing_voters_with_admin_url_and_count_votes_if_does_not_votes(self):

        result = self.PollAdmin.get_listing_voters_with_admin_url_and_count_votes()

        self.assertEqual(result, '<i>No-one yet not participated in polls.</i>')

    def test_get_listing_voters_with_admin_url_and_count_votes_if_exists_one_voter(self):

        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)
        result = self.PollAdmin.get_listing_voters_with_admin_url_and_count_votes()

        self.assertEqual(result, '<a href="{0}">{1} (1 vote)</a>'.format(
            self.active_superuser.get_admin_url(),
            self.active_superuser.get_full_name(),
        ))

    def test_get_listing_voters_with_admin_url_and_count_votes_if_exists_two_voters(self):

        # user1 has 1 vote, user2 has 2 votes
        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)
        Vote.objects.create(user=self.user2, poll=self.poll1, choice=self.choice11)
        Vote.objects.create(user=self.user2, poll=self.poll2, choice=self.choice21)

        result = self.PollAdmin.get_listing_voters_with_admin_url_and_count_votes()

        self.assertEqual(result, '<a href="{2}">{3} (2 votes)</a>, <a href="{0}">{1} (1 vote)</a>'.format(
            self.active_superuser.get_admin_url(),
            self.active_superuser.get_full_name(),
            self.user2.get_admin_url(),
            self.user2.get_full_name(),
        ))

    def test_get_listing_voters_with_admin_url_and_count_votes_if_exists_three_voters(self):

        # user1 has 1 vote, user2 has 3 votes, user3 has 2 votes
        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)
        Vote.objects.create(user=self.user2, poll=self.poll1, choice=self.choice11)
        Vote.objects.create(user=self.user2, poll=self.poll2, choice=self.choice21)
        Vote.objects.create(user=self.user2, poll=self.poll3, choice=self.choice31)
        Vote.objects.create(user=self.user3, poll=self.poll1, choice=self.choice11)
        Vote.objects.create(user=self.user3, poll=self.poll2, choice=self.choice21)

        result = self.PollAdmin.get_listing_voters_with_admin_url_and_count_votes()

        self.assertEqual(
            result,
            '<a href="{2}">{3} (3 votes)</a>, <a href="{4}">{5} (2 votes)</a>, <a href="{0}">{1} (1 vote)</a>'.format(
                self.active_superuser.get_admin_url(),
                self.active_superuser.get_full_name(),
                self.user2.get_admin_url(),
                self.user2.get_full_name(),
                self.user3.get_admin_url(),
                self.user3.get_full_name(),
            )
        )

    def test_get_most_popular_choice_or_choices_as_html_if_poll_has_not_choices(self):

        self.poll1.choices.filter().delete()
        result = self.PollAdmin.get_most_popular_choice_or_choices_as_html(self.poll1)
        self.assertEqual(result, '<i>Poll does not have a choices at all.</i>')

    def test_get_most_popular_choice_or_choices_as_html_if_poll_has_single_most_popular_choice(self):

        result = self.PollAdmin.get_most_popular_choice_or_choices_as_html(self.poll1)
        self.assertEqual(result, '<li style="list-style: none;">{0} (0 votes)</li>'.format(
            self.choice11.get_truncated_text_choice(),
        ))

    def test_get_most_popular_choice_or_choices_as_html_if_poll_has_single_most_popular_choice2(self):

        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)

        result = self.PollAdmin.get_most_popular_choice_or_choices_as_html(self.poll1)

        self.assertEqual(result, '<li style="list-style: none;">{0} (1 vote)</li>'.format(
            self.choice11.get_truncated_text_choice(),
        ))

    def test_get_most_popular_choice_or_choices_as_html_if_poll_has_several_most_popular_choices(self):

        choice12 = ChoiceFactory(poll=self.poll1)

        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)
        Vote.objects.create(user=self.user2, poll=self.poll1, choice=choice12)

        result = self.PollAdmin.get_most_popular_choice_or_choices_as_html(self.poll1)
        self.assertIn(
            '<li style="list-style: none;">{0} (1 vote)</li>'.format(self.choice11.get_truncated_text_choice()),
            result
        )
        self.assertIn(
            '<li style="list-style: none;">{0} (1 vote)</li>'.format(choice12.get_truncated_text_choice()),
            result
        )

    def test_colored_status_display(self):
        self.assertEqual(
            self.PollAdmin.colored_status_display(self.poll1),
            '<span style="color: rgb(0, 255, 0)">{0}</span>'.format(self.poll1.get_status_display())
        )
        self.assertEqual(
            self.PollAdmin.colored_status_display(self.poll2),
            '<span style="color: rgb(0, 0, 255)">{0}</span>'.format(self.poll2.get_status_display())
        )
        self.assertEqual(
            self.PollAdmin.colored_status_display(self.poll3),
            '<span style="color: rgb(255, 0, 0)">{0}</span>'.format(self.poll3.get_status_display())
        )

    def test__build_chart_poll_result(self):

        chart_polls_statistics = self.PollAdmin._build_chart_poll_result(self.poll1.pk)
        self.assertEqual(magic.from_buffer(chart_polls_statistics, mime=True), 'application/xml')

    def test__build_chart_polls_statistics(self):

        chart_polls_statistics = self.PollAdmin._build_chart_polls_statistics()
        self.assertEqual(magic.from_buffer(chart_polls_statistics, mime=True), 'application/xml')

    @pytest.mark.xfail(reason='Not implemented Preview for poll in Admin')
    def test_view_preview(self):
        raise NotImplementedError

    def test_basic_view_statistics(self):

        url = self.reverse('admin:polls_statistics')

        request = self.factory.get(url)
        request.user = self.active_superuser

        response = self.PollAdmin.view_statistics(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'polls/admin/statistics.html')

        context_data = response.context_data
        self.assertEqual(context_data['current_app'], apps.get_app_config(Poll._meta.app_label))
        self.assertEqual(force_text(context_data['title']), 'Statistics about polls')
        self.assertEqual(
            magic.from_buffer(context_data['chart_statistics_count_votes_by_year'], mime=True),
            'application/xml',
        )

        self.assertIsInstance(context_data['django_admin_media'], widgets.Media)

    def test_context_statistis_view_statistics_if_no_exists_votes(self):

        Choice.objects.filter().delete()

        response = self.PollAdmin.view_statistics(self.request_for_view_statistics)

        context_statistics = response.context_data['statistics']
        self.assertEqual(context_statistics['count_polls'], 3)
        self.assertEqual(context_statistics['count_opened_polls'], 1)
        self.assertEqual(context_statistics['count_closed_polls'], 1)
        self.assertEqual(context_statistics['count_draft_polls'], 1)
        self.assertEqual(context_statistics['count_choices'], 0)
        self.assertEqual(context_statistics['count_votes'], 0)
        self.assertEqual(context_statistics['count_voters'], 0)
        self.assertIsNone(context_statistics['date_latest_vote'])
        self.assertIsNone(context_statistics['latest_active_poll'])
        self.assertIsNone(context_statistics['latest_voter'])
        self.assertIsNone(context_statistics['latest_selected_choice'])
        self.assertEqual(context_statistics['all_voters'], '<i>No-one yet not participated in polls.</i>')

    def test_context_statistis_view_statistics_if_exists_one_vote(self):

        vote = Vote.objects.create(user=self.user2, poll=self.poll2, choice=self.choice21)

        response = self.PollAdmin.view_statistics(self.request_for_view_statistics)

        context_statistics = response.context_data['statistics']
        self.assertEqual(context_statistics['count_polls'], 3)
        self.assertEqual(context_statistics['count_opened_polls'], 1)
        self.assertEqual(context_statistics['count_closed_polls'], 1)
        self.assertEqual(context_statistics['count_draft_polls'], 1)
        self.assertEqual(context_statistics['count_choices'], 3)
        self.assertEqual(context_statistics['count_votes'], 1)
        self.assertEqual(context_statistics['count_voters'], 1)
        self.assertEqual(context_statistics['date_latest_vote'], vote.date_voting)
        self.assertEqual(context_statistics['latest_active_poll'], self.poll2)
        self.assertEqual(context_statistics['latest_voter'], self.user2)
        self.assertEqual(context_statistics['latest_selected_choice'], self.choice21)
        self.assertEqual(context_statistics['all_voters'], '<a href="{0}">{1} (1 vote)</a>'.format(
            self.user2.get_admin_url(),
            self.user2.get_full_name(),
        ))

    def test_context_statistis_view_statistics_if_exists_several_votes(self):

        # user1 has 2 votes, user2 has 1 vote, user3 has 3 votes
        Vote.objects.create(user=self.active_superuser, poll=self.poll1, choice=self.choice11)
        Vote.objects.create(user=self.active_superuser, poll=self.poll2, choice=self.choice21)
        Vote.objects.create(user=self.user2, poll=self.poll2, choice=self.choice21)
        Vote.objects.create(user=self.user3, poll=self.poll3, choice=self.choice31)
        Vote.objects.create(user=self.user3, poll=self.poll1, choice=self.choice11)
        vote = Vote.objects.create(user=self.user3, poll=self.poll2, choice=self.choice21)

        response = self.PollAdmin.view_statistics(self.request_for_view_statistics)

        context_statistics = response.context_data['statistics']
        self.assertEqual(context_statistics['count_polls'], 3)
        self.assertEqual(context_statistics['count_opened_polls'], 1)
        self.assertEqual(context_statistics['count_closed_polls'], 1)
        self.assertEqual(context_statistics['count_draft_polls'], 1)
        self.assertEqual(context_statistics['count_choices'], 3)
        self.assertEqual(context_statistics['count_votes'], 6)
        self.assertEqual(context_statistics['count_voters'], 3)
        self.assertEqual(context_statistics['date_latest_vote'], vote.date_voting)
        self.assertEqual(context_statistics['latest_active_poll'], self.poll2)
        self.assertEqual(context_statistics['latest_voter'], self.user3)
        self.assertEqual(context_statistics['latest_selected_choice'], self.choice21)
        self.assertEqual(
            context_statistics['all_voters'],
            '<a href="{4}">{5} (3 votes)</a>, <a href="{0}">{1} (2 votes)</a>, <a href="{2}">{3} (1 vote)</a>'.format(
                self.active_superuser.get_admin_url(),
                self.active_superuser.get_full_name(),
                self.user2.get_admin_url(),
                self.user2.get_full_name(),
                self.user3.get_admin_url(),
                self.user3.get_full_name(),
            )
        )

    def test_view_make_report_throught_GET(self):

        request = self.factory.get(self.url_polls_make_report)
        request.user = self.active_superuser
        response = self.PollAdmin.view_make_report(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'polls/admin/report.html')
        self.assertEqual(force_text(response.context_data['title']), 'Make a report about polls')
        self.assertEqual(response.context_data['current_app'], apps.get_app_config(Poll._meta.app_label))
        self.assertIsInstance(response.context_data['django_admin_media'], widgets.Media)

    def test_view_make_report_throught_POST_without_specified_output_report(self):

        request = self.factory.post(self.url_polls_make_report, {})
        request.user = self.active_superuser
        response = self.PollAdmin.view_make_report(request)

        self.assertContains(response, 'Not specified any theme for report.', status_code=400)

    def test_view_make_report_throught_POST_without_specified_themes_of_excel_report(self):

        request = self.factory.post(self.url_polls_make_report, {'output_report': 'report_excel'})
        request.user = self.active_superuser
        response = self.PollAdmin.view_make_report(request)

        self.assertContains(response, 'Not specified any theme for report.', status_code=400)

    def test_view_make_report_throught_POST_without_specified_themes_of_pdf_report(self):

        request = self.factory.post(self.url_polls_make_report, {'output_report': 'report_pdf'})
        request.user = self.active_superuser
        response = self.PollAdmin.view_make_report(request)

        self.assertContains(response, 'Not specified any theme for report.', status_code=400)

    def test_view_make_report_throught_POST_without_specified_type_of_report_but_with_themes(self):

        request = self.factory.post(self.url_polls_make_report, {'votes': 'votes'})
        request.user = self.active_superuser
        response = self.PollAdmin.view_make_report(request)

        self.assertContains(response, 'Type of report is not supplied.', status_code=400)

    @mock.patch('django.utils.timezone.now')
    def test_view_make_report_throught_POST_for_excel_report_on_different_themes(self, mock_now):

        mock_now.return_value = self.timezone.datetime(2018, 4, 1, 11, 18, tzinfo=self.timezone.utc)

        data = {
            'polls': 'polls',
            'choices': 'choices',
            'votes': 'votes',
            'results': 'results',
            'voters': 'voters',
            'output_report': 'report_excel',
        }

        request = self.factory.post(self.url_polls_make_report, data)
        request.user = self.active_superuser

        # keep time on start request
        # now = timezone.now()

        response = self.PollAdmin.view_make_report(request)

        self.assertEqual(magic.from_buffer(response.getvalue(), mime=True), 'application/zip')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Type'),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn(
            response.get('Content-Disposition'),
            'attachment; filename=Report about polls 2018-04-01 11:18:00.xlsx'
        )

    @mock.patch('django.utils.timezone.now')
    def test_view_make_report_throught_POST_for_pdf_report_on_different_themes(self, mock_now):

        mock_now.return_value = self.timezone.datetime(2016, 11, 11, 1, 8, 7, tzinfo=self.timezone.utc)

        data = {
            'polls': 'polls',
            'choices': 'choices',
            'votes': 'votes',
            'results': 'results',
            'voters': 'voters',
            'output_report': 'report_pdf',
        }

        request = self.factory.post(self.url_polls_make_report, data)
        request.user = self.active_superuser

        response = self.PollAdmin.view_make_report(request)

        self.assertEqual(magic.from_buffer(response.getvalue(), mime=True), 'application/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
        self.assertIn(
            response.get('Content-Disposition'),
            'attachment; filename=Report about polls 2016-11-11 01:08:07.pdf'
        )


class ChoiceAdminTests(EnhancedTestCase):

    @classmethod
    def setUpTestData(cls):

        call_command('factory_test_users', '3')
        cls.active_superuser, cls.user2, cls.user3 = cls.django_user_model.objects.all()
        cls._make_user_as_active_superuser(cls.active_superuser)

        cls.ChoiceAdmin = ChoiceAdmin(Choice, AdminSite)

        cls.poll = PollFactory()
        cls.choice1 = ChoiceFactory(poll=cls.poll)
        cls.choice2 = ChoiceFactory(poll=cls.poll)
        cls.choice3 = ChoiceFactory(poll=cls.poll)

    def setUp(self):
        self.client.force_login(self.active_superuser)

    def test_get_queryset(self):
        qs = self.ChoiceAdmin.get_queryset(self.mockrequest)
        self.assertIn('count_votes', qs.values()[0])

    def test_get_urls(self):
        urls = self.ChoiceAdmin.get_urls()

        urls_names = list()
        for url in urls:
            if url.name == 'polls_choice_change':
                url_polls_choice_change = url
            urls_names.append(url.name)

        self.assertNotIn('polls_choice_add', urls_names)
        self.assertNotIn('polls_choice_history', urls_names)
        self.assertNotIn('polls_choice_delete', urls_names)
        self.assertEqual(url_polls_choice_change.regex.pattern, '^(.+)/preview/$')

    def test_template_used_in_change_view(self):

        url = self.reverse('admin:polls_choice_change', args=[self.choice1.pk])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'polls/admin/choice_preview_form.html')

    def test_accessibility_urls(self):

        urls = self.ChoiceAdmin.get_urls()

        for url in urls:
            if url.name == 'polls_choice_changelist':
                urlpath = self.reverse('admin:polls_choice_changelist')
            elif url.name == 'polls_choice_change':
                urlpath = self.reverse('admin:polls_choice_change', args=[self.choice1.pk])

            response = self.client.get(urlpath)
            self.assertEqual(response.status_code, 200)

    def test_get_voters_with_get_admin_links_as_html_if_no_voters(self):

        result = self.ChoiceAdmin.get_voters_with_get_admin_links_as_html(self.choice1)
        self.assertEqual(result, '<i>Nothing voted for this choice.</i>')

    def test_get_voters_with_get_admin_links_as_html_if_exists_single_voter(self):

        Vote.objects.create(user=self.active_superuser, poll=self.poll, choice=self.choice1)

        result = self.ChoiceAdmin.get_voters_with_get_admin_links_as_html(self.choice1)
        self.assertEqual(result, '<span><a href="{0}">{1}</a></span>'.format(
            self.active_superuser.get_admin_url(),
            self.active_superuser.get_full_name(),
        ))

    def test_get_voters_with_get_admin_links_as_html_if_exists_several_voters(self):

        Vote.objects.create(user=self.active_superuser, poll=self.poll, choice=self.choice1)
        Vote.objects.create(user=self.user2, poll=self.poll, choice=self.choice1)
        Vote.objects.create(user=self.user3, poll=self.poll, choice=self.choice1)

        result = self.ChoiceAdmin.get_voters_with_get_admin_links_as_html(self.choice1)
        self.assertIn(
            '<span><a href="{0}">{1}</a></span>'.format(
                self.active_superuser.get_admin_url(),
                self.active_superuser.get_full_name(),
            ),
            result
        )
        self.assertIn(
            '<span><a href="{0}">{1}</a></span>'.format(
                self.user2.get_admin_url(),
                self.user2.get_full_name(),
            ),
            result
        )
        self.assertIn(
            '<span><a href="{0}">{1}</a></span>'.format(
                self.user3.get_admin_url(),
                self.user3.get_full_name(),
            ),
            result
        )

    def test_get_poll_admin_link_as_html(self):

        result = self.ChoiceAdmin.get_poll_admin_link_as_html(self.choice1)
        self.assertEqual(result, '<a href="{0}">{1}</a>'.format(
            self.choice1.poll.get_admin_url(),
            self.choice1.poll)
        )


class VoteAdminTests(EnhancedTestCase):

    @classmethod
    def setUpTestData(cls):

        call_command('factory_test_users', '1')

        cls.active_superuser = cls.django_user_model.objects.get()
        cls._make_user_as_active_superuser(cls.active_superuser)

        poll = PollFactory()
        choice = ChoiceFactory(poll=poll)
        cls.vote = Vote.objects.create(poll=poll, choice=choice, user=cls.active_superuser)

        cls.VoteAdmin = VoteAdmin(Vote, AdminSite)

    def setUp(self):
        self.client.force_login(self.active_superuser)

    def test_get_urls(self):
        urls = self.VoteAdmin.get_urls()
        urls_names = [url.name for url in urls]

        self.assertNotIn('polls_vote_add', urls_names)
        self.assertNotIn('polls_vote_change', urls_names)
        self.assertNotIn('polls_vote_history', urls_names)
        self.assertNotIn('polls_vote_delete', urls_names)

    def test_accessibility_urls(self):

        urls = self.VoteAdmin.get_urls()

        for url in urls:
            if url.name == 'polls_vote_changelist':
                urlpath = self.reverse('admin:polls_vote_changelist')
                response = self.client.get(urlpath)
                self.assertEqual(response.status_code, 200)
