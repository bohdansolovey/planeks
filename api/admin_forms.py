from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms

from .models import AuthUser, Comment


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput, required=False
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput, required=False
    )

    class Meta:
        model = AuthUser
        exclude = ('last_login', 'join_date', )
        readonly_fields = []

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        if password2 == '':
            return None
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password2"])
        if commit:
            user.save()
        return user


class UserPasswordChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        help_text=("Raw passwords are not stored, so there is no way to see "
                   "this user's password, but you can change the password "
                   "using <a href=\"../password/\">this form</a>."), )

    class Meta:
        model = AuthUser
        fields = ('email', )

    def clean_password(self):
        return self.initial["password"]


class CommentAddForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ('date_created', )