from django import forms
from django.core.validators import RegexValidator

from web.models.roles import Role
from web.models.users import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'username': forms.TextInput()
        }


class InviteForm(forms.Form):
    _selected_user = forms.IntegerField(widget=forms.MultipleHiddenInput, required=False)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'vTextField'}))
    roles = forms.ModelMultipleChoiceField(label='Роли', queryset=Role.objects.exclude(slug__in=['everyone', 'registered']), required=False)


class CreateAccountForm(forms.Form):
    username = forms.CharField(label='Имя пользователя', required=True, validators=[RegexValidator(r'^[A-Za-z0-9_-]+$', 'Некорректное имя пользователя')])
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput(), required=True)

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают')
        return cd['password2']


class CreateBotForm(forms.Form):
    username = forms.CharField(
        label='Ник бота',
        required=True,
        validators=[
                RegexValidator(r'^[A-Za-z0-9_-]+$', 'Некорректное имя пользователя')
            ]
        )


class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Никнейм',
        required=True,
        max_length=150,
        validators=[RegexValidator(r'^[\w.-]+\Z', 'Некорректное имя пользователя. Разрешённые символы: A-Z, a-z, 0-9, -, _.')],
        widget=forms.TextInput(attrs={'autofocus': '', 'autocapitalize': 'none', 'autocomplete': 'username'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    password = forms.CharField(
        label='Пароль',
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с данным именем уже существует')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с данным email уже существует')
        return email

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError('Введенные пароли не совпадают')
        return password2