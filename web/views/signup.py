from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import AbstractUser as _UserType
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth import login
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.db import IntegrityError
from django.urls import reverse

import re

from web.models.users import UsedToken
from web.models.roles import Role
from web.models.site import get_current_site
from web.forms import RegisterForm
from .invite import account_activation_token
from web.events import EventBase


User = get_user_model()


class OnUserSignUp(EventBase, name='on_user_signup'):
    request: HttpRequest
    user: _UserType


def _assign_default_role(user):
    """
    Присваивает пользователю роль по умолчанию, если она задана в настройках.
    Роль должна существовать заранее — автоматического создания не происходит.
    """
    role_slug = getattr(settings, 'DEFAULT_USER_ROLE', None)
    if not role_slug:
        return
    try:
        role = Role.objects.get(slug=role_slug)
        user.roles.add(role)
    except Role.DoesNotExist:
        pass


class AcceptInvitationView(TemplateResponseMixin, ContextMixin, View):
    template_name = "signup/accept.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_user(self):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user

    def get(self, request, *args, **kwargs):
        if not isinstance(request.user, AnonymousUser):
            return HttpResponseRedirect(redirect_to=settings.LOGIN_REDIRECT_URL)
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        user = self.get_user()
        if UsedToken.is_used(self.kwargs['token']) or not account_activation_token.check_token(user, self.kwargs["token"]):
            context.update({'error': 'Некорректное приглашение.', 'error_fatal': True})
            return self.render_to_response(context)
        if user.type == User.UserType.Wikidot:
            context.update({'is_wikidot': True, 'username': user.wikidot_username})
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        user = self.get_user()
        if UsedToken.is_used(self.kwargs['token']) or not account_activation_token.check_token(user, self.kwargs['token']):
            context.update({'error': 'Некорректное приглашение.', 'error_fatal': True})
            return self.render_to_response(context)
        if user.type == User.UserType.Wikidot:
            username = user.wikidot_username
            context.update({'is_wikidot': True})
        else:
            username = request.POST.get('username', '').strip()
        context.update({'username': username})
        password1 = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        # check if username is not valid
        if not re.match(r"^[\w.-]+\Z", username, re.ASCII):
            context.update({'error': 'Некорректное имя пользователя. Разрешённые символы: A-Z, a-z, 0-9, -, _.'})
            return self.render_to_response(context)
        # check if user already exists
        user_exists = User.objects.filter(username=username)
        wd_user_exists = User.objects.filter(wikidot_username=username)
        if (user_exists and user_exists[0] != user) or (wd_user_exists and wd_user_exists[0] != user):
            context.update({'error': 'Выбранное имя пользователя уже используется.'})
            return self.render_to_response(context)
        if not password1:
            context.update({'error': 'Пароль должен быть указан.'})
            return self.render_to_response(context)
        if password1 != password2:
            context.update({'error': 'Введенные пароли не совпадают.'})
            return self.render_to_response(context)
        if user.type != User.UserType.Wikidot:
            user.username = username
        else:
            user.username = user.wikidot_username
            user.type = User.UserType.Normal
        user.set_password(password1)
        user.is_active = True
        user.save()
        UsedToken.mark_used(self.kwargs['token'], is_case_sensitive=True)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        OnUserSignUp(request, user).emit()
        return HttpResponseRedirect(redirect_to=settings.LOGIN_REDIRECT_URL)


class RegisterView(TemplateResponseMixin, ContextMixin, View):
    template_name = "signup/register.html"
    form_class = RegisterForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not isinstance(request.user, AnonymousUser):
            return HttpResponseRedirect(redirect_to=settings.LOGIN_REDIRECT_URL)
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        context['form'] = self.form_class()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if not isinstance(request.user, AnonymousUser):
            return HttpResponseRedirect(redirect_to=settings.LOGIN_REDIRECT_URL)

        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        form = self.form_class(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False
                )

                _assign_default_role(user)

                site = get_current_site()
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = account_activation_token.make_token(user)
                activation_url = request.build_absolute_uri(
                    reverse('activate_account', kwargs={'uidb64': uid, 'token': token})
                )
                subject = f"Подтверждение регистрации на {site.title}"
                c = {
                    "email": user.email,
                    'domain': request.get_host(),
                    'site_name': site.title,
                    "uid": uid,
                    "user": user,
                    'token': token,
                    'protocol': request.scheme,
                    'activation_url': activation_url,
                }
                content = render_to_string("mails/activation_email.txt", c, request=request)
                try:
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
                    send_mail(subject, content, from_email, [user.email], fail_silently=False)
                    context['success'] = True
                    context['message'] = 'Письмо с подтверждением отправлено на ваш email. Пожалуйста, проверьте почту и перейдите по ссылке для активации аккаунта.'
                except BadHeaderError:
                    context['error'] = 'Ошибка при отправке письма. Пожалуйста, попробуйте позже.'
                    user.delete()
            except IntegrityError:
                context['error'] = 'Ошибка при создании аккаунта. Возможно, пользователь с таким именем или email уже существует.'
        else:
            context['form'] = form
            if form.errors:
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(error)
                context['error'] = ' '.join(error_messages)

        return self.render_to_response(context)


class ActivateAccountView(TemplateResponseMixin, ContextMixin, View):
    template_name = "signup/activate.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_user(self):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user

    def get(self, request, *args, **kwargs):
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        user = self.get_user()

        if user is None:
            context['error'] = 'Некорректная ссылка активации.'
            context['error_fatal'] = True
            return self.render_to_response(context)

        if UsedToken.is_used(self.kwargs['token']):
            context['error'] = 'Ссылка активации уже была использована.'
            context['error_fatal'] = True
            return self.render_to_response(context)

        if not account_activation_token.check_token(user, self.kwargs["token"]):
            context['error'] = 'Некорректная или устаревшая ссылка активации.'
            context['error_fatal'] = True
            return self.render_to_response(context)

        user.is_active = True
        user.save()

        UsedToken.mark_used(self.kwargs['token'], is_case_sensitive=True)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        OnUserSignUp(request, user).emit()

        return HttpResponseRedirect(redirect_to=settings.LOGIN_REDIRECT_URL)
