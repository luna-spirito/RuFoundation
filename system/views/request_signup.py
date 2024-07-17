from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.core.mail import send_mail, BadHeaderError
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.shortcuts import redirect, resolve_url
from django.contrib.auth import get_user_model
from django.views.generic import FormView
from django.contrib.admin import site
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView, RedirectURLMixin

from system.forms import InviteForm, RequestSignupForm
from system.views.invite import InviteView
from web.models.sites import get_current_site

class RequestSignupView(FormView):
    form_class = RequestSignupForm
    template_name="login/request_signup.html"

    def form_valid(self, form):
        password_reset_form = PasswordResetForm(data = form.cleaned_data) # I'm sorry
        password_reset_form.full_clean() # I'm sorry
        if next(password_reset_form.get_users(password_reset_form.cleaned_data["email"]), None) is not None: # Oh my god, I'm so sorry
            return PasswordResetView(request = self.request, next_page = self.next_page).form_valid(password_reset_form) # Sorry!
        else:
            invite_form = InviteForm(data = form.cleaned_data)
            invite_form.full_clean()
            InviteView(request = self.request, kwargs = {}).form_valid(invite_form)
            return redirect("/") # ... sorry...
