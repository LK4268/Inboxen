##
#    Copyright (C) 2013 Jessica Tallon & Matt Molyneaux
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

from django.utils.translation import ugettext as _
from django.db.models import F, Q
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from django.views import generic
from inboxen import models
from website.views import base

from queue.delete.tasks import delete_email

class InboxView(
                base.CommonContextMixin,
                base.LoginRequiredMixin,
                generic.ListView
                ):
    """Base class for Inbox views"""
    model = models.Email
    paginate_by = 100

    def get_success_url(self):
        """Override this method to return the URL to return the user to"""
        raise NotImplementedError

    def get_queryset(self, *args, **kwargs):
        qs = super(InboxView, self).get_queryset(*args, **kwargs)
        qs = qs.order_by("-received_date").select_related("inbox", "inbox__domain")
        return qs

    def post(self, *args, **kwargs):
        qs = self.get_queryset()

        # this is kinda bad, but nested forms aren't supported in all browsers
        if "delete-single" in self.request.POST:
            email_id = int(self.request.POST["delete-single"], 16)
            email = qs.get(id=email_id)
            email.delete()
            return HttpResponseRedirect(self.get_success_url())

        emails = Q(id=None)
        for email in self.request.POST:
            if self.request.POST[email] == "email":
                try:
                    email_id = int(email, 16)
                    emails = emails | Q(id=email_id)
                except (self.model.DoesNotExist, ValueError):
                    return

        # update() & delete() like to do a select first for some reason :s
        emails = qs.filter(emails)

        if "read" in self.request.POST:
            emails.update(flags=F('flags').bitand(~self.model.flags.read))
        elif "unread" in self.request.POST:
            emails.update(flags=F('flags').bitor(self.model.flags.read))
        elif "delete" in self.request.POST:
            emails.update(flags=F('flags').bitor(self.model.flags.deleted))
            for email in emails:
                delete_email.delay(email.id)

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, *args, **kwargs):
        headers = models.Header.objects.filter(part__parent=None, part__email__in=self.object_list)
        headers = headers.get_many("Subject", "From", group_by="part__email_id")

        for email in self.object_list:
            header_set = headers[email.id]
            email.subject = header_set.get("Subject")
            email.sender = header_set["From"]

        return super(InboxView, self).get_context_data(*args, **kwargs)


class UnifiedInboxView(InboxView):
    """View all inboxes together"""
    def get_success_url(self):
        return reverse('unified-inbox')

    def get_queryset(self, *args, **kwargs):
        qs = super(UnifiedInboxView, self).get_queryset(*args, **kwargs)
        qs = qs.filter(inbox__user=self.request.user)
        return qs

    def get_context_data(self, *args, **kwargs):
        self.title = _("Inbox")
        return super(UnifiedInboxView, self).get_context_data(*args, **kwargs)

class SingleInboxView(UnifiedInboxView):
    """View a single inbox"""
    def get_success_url(self):
        return reverse('single-inbox', kwargs={"inbox": self.kwargs["inbox"], "domain": self.kwargs["domain"]})

    def get_queryset(self, *args, **kwargs):
        qs = super(SingleInboxView, self).get_queryset(*args, **kwargs)
        qs = qs.filter(inbox__inbox=self.kwargs["inbox"], inbox__domain__domain=self.kwargs["domain"])
        return qs

    def get_context_data(self, *args, **kwargs):
        self.title = "{0}@{1}".format(self.kwargs["inbox"], self.kwargs["domain"])
        context = super(UnifiedInboxView, self).get_context_data(*args, **kwargs)
        context.update({"inbox":self.kwargs["inbox"], "domain":self.kwargs["domain"]})

        return context
