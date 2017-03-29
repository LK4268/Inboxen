##
#    Copyright (C) 2014 Jessica Tallon & Matt Molyneaux
#
#    This file is part of Inboxen.
#
#    Inboxen is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Inboxen is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with Inboxen.  If not, see <http://www.gnu.org/licenses/>.
##

from django import test
from django.core import mail, urlresolvers
from django.db.models import Max

from wagtail.wagtailcore.models import Site
import factory
import factory.fuzzy

from cms.models import AppPage, HelpIndex
from cms.utils import app_reverse
from inboxen.tests import factories
from inboxen.utils import override_settings
from tickets import models
from tickets.templatetags import tickets_flags


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Question

    author = factory.SubFactory(factories.UserFactory)
    subject = factory.fuzzy.FuzzyText()
    body = factory.fuzzy.FuzzyText()


class ResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Response

    author = factory.SubFactory(factories.UserFactory)
    body = factory.fuzzy.FuzzyText()
    question = factory.SubFactory(QuestionFactory)


class MockModel(models.RenderBodyMixin):
    def __init__(self, body):
        self.body = body


class QuestionViewTestCase(test.TestCase):
    def setUp(self):
        super(QuestionViewTestCase, self).setUp()
        self.user = factories.UserFactory()
        self.other_user = factories.UserFactory(username="tester")

        QuestionFactory.create_batch(11, author=self.user, status=models.Question.NEW)
        QuestionFactory.create_batch(3, author=self.other_user, status=models.Question.RESOLVED)

        self.page = AppPage.objects.get(app="tickets.urls")
        self.site = Site.objects.get(is_default_site=True)

        login = self.client.login(username=self.user.username, password="123456")

        if not login:
            raise Exception("Could not log in")

    def get_url(self):
        return app_reverse(self.page, self.site, "tickets-index")

    def test_get(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

        self.assertIn("More Questions", response.content)
        list_url = app_reverse(self.page, self.site, "tickets-list", kwargs={"status": "open"})
        self.assertIn(list_url, response.content)

    def test_switch_open_closed(self):
        models.Question.objects.filter(status=models.Question.NEW).update(author=self.other_user)
        models.Question.objects.filter(status=models.Question.RESOLVED).update(author=self.user)

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

        self.assertIn("More Questions", response.content)
        list_url = app_reverse(self.page, self.site, "tickets-list", kwargs={"status": "closed"})
        self.assertIn(list_url, response.content)

    def test_post(self):
        params = {"subject": "hello!", "body": "This is the body of my question"}
        response = self.client.post(self.get_url(), params)
        question = models.Question.objects.latest("date")

        expected_url = app_reverse(self.page, self.site, "tickets-detail", kwargs={"pk": question.pk})
        self.assertRedirects(response, expected_url)

        self.assertEqual(question.author_id, self.user.id)
        self.assertEqual(question.body, "This is the body of my question")


class QuestionDetailTestCase(test.TestCase):
    def setUp(self):
        super(QuestionDetailTestCase, self).setUp()
        self.user = factories.UserFactory()
        self.other_user = factories.UserFactory(username="tester")

        self.question = QuestionFactory(author=self.user, status=models.Question.NEW)
        self.page = AppPage.objects.get(app="tickets.urls")
        self.site = Site.objects.get(is_default_site=True)

        login = self.client.login(username=self.user.username, password="123456")

        if not login:
            raise Exception("Could not log in")

    def get_url(self):
        return app_reverse(self.page, self.site, "tickets-detail", kwargs={"pk": self.question.pk})

    def test_get(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.question.render_body(), response.content)

    def test_post(self):
        response = self.client.post(self.get_url(), {"body": "hello"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.get_url())

        responses = self.question.response_set.all()
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0].author, self.user)
        self.assertEqual(responses[0].body, "hello")

        response = self.client.get(self.get_url())
        self.assertIn(responses[0].render_body(), response.content)


class QuestionListTestCase(test.TestCase):
    def setUp(self):
        super(QuestionListTestCase, self).setUp()
        self.user = factories.UserFactory()

        QuestionFactory.create_batch(75, author=self.user, status=models.Question.NEW)

        self.page = AppPage.objects.get(app="tickets.urls")
        self.site = Site.objects.get(is_default_site=True)

        login = self.client.login(username=self.user.username, password="123456")

        if not login:
            raise Exception("Could not log in")

    def get_url(self):
        return app_reverse(self.page, self.site, "tickets-list", kwargs={"status": "open"})

    def test_get(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.get_url() + "2/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.get_url() + "3/")
        self.assertEqual(response.status_code, 404)


@override_settings(ADMINS=(("admin", "root@localhost"),))
class QuestionModelTestCase(test.TestCase):
    def setUp(self):
        super(QuestionModelTestCase, self).setUp()
        self.user = factories.UserFactory()

    def test_admins_emailed(self):
        question = models.Question()
        question.author = self.user
        question.subject = "Hey"
        question.body = "Sort it out!"

        question.save()

        self.assertEqual(len(mail.outbox), 1)

        question2 = models.Question.objects.get(id=question.id)
        question2.save()

        self.assertEqual(len(mail.outbox), 1)

    def test_last_activity(self):
        question = models.Question()
        question.author = self.user
        question.subject = "Hey"
        question.body = "Sort it out!"
        question.save()
        question.refresh_from_db()

        question_qs = models.Question.objects.annotate(last_response_date=Max("response__date"))
        self.assertEqual(question_qs[0].last_activity, question.last_modified)

        response = models.Response()
        response.question = question
        response.author = self.user
        response.body = "Oook"
        response.save()
        response.refresh_from_db()

        question_qs = models.Question.objects.annotate(last_response_date=Max("response__date"))
        self.assertEqual(question_qs[0].last_activity, response.date)

    def test_unicode(self):
        question = QuestionFactory(author=self.user)
        self.assertEqual(type(question.__unicode__()), unicode)

        response = ResponseFactory(question=question, author=self.user)
        self.assertEqual(type(response.__unicode__()), unicode)


class RenderBodyTestCase(test.TestCase):
    def test_empty_body(self):
        obj = MockModel("")
        self.assertEqual(obj.render_body(), "")

    def assertHtmlEqual(self, first, second, *args):
        """Normalise HTML and compare

        LXML seems to deal with whitespace differently on different systems, so
        we strip it out before comparing
        """
        first = "".join(first.split())
        second = "".join(second.split())

        self.assertEqual(first, second, *args)

    def test_normal_html(self):
        original = "Hi\n\nAnother < 12\n\n* this one\n* that one"""
        expected = "<div><p>Hi</p>\n<p>Another &lt; 12</p>\n<ul>\n<li>this one</li>\n<li>that one</li>\n</ul></div>"
        obj = MockModel(original)
        self.assertHtmlEqual(obj.render_body(), expected)

    def test_bad_html(self):
        original = "<p class='hide'>Hi</p>\n\n<sometag> </>"
        expected = "<div><p>Hi</p>\n\n<p> &gt;</p></div>"
        obj = MockModel(original)
        self.assertHtmlEqual(obj.render_body(), expected)


class RenderStatus(test.TestCase):
    def test_render(self):
        result = tickets_flags.render_status(models.Question.NEW)
        self.assertIn(unicode(tickets_flags.STATUSES[models.Question.NEW]), result)
        self.assertIn(unicode(tickets_flags.STATUS_TO_TAGS[models.Question.NEW]["class"]), result)

        self.assertNotEqual(tickets_flags.render_status(models.Question.RESOLVED), result)
