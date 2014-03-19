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

from datetime import datetime

from pytz import utc

from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.views import generic
from django.core.urlresolvers import reverse_lazy

from inboxen.models import Inbox

from website import forms
from website.views import base

class InboxAddView(base.CommonContextMixin, base.LoginRequiredMixin, generic.CreateView):
    title = "Add Inbox"
    success_url = reverse_lazy('user-home')
    form_class = forms.InboxAddForm
    model = Inbox
    template_name = "email/add.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.userprofile.available_inboxes() <= 0:
            ## TODO: add django message's error: you have too many inboxes
            return HttpResponseRedirect(self.success_url)

        return super(InboxAddView, self).dispatch(request=request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(InboxAddView, self).get_form_kwargs(*args, **kwargs)
        kwargs.setdefault("request", self.request)
        return kwargs
