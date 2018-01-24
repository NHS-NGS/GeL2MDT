from django import forms
from .models import *
from django.contrib.auth.models import User

class UserForm(forms.ModelForm):
    """ User registration form
    """
    password = forms.CharField(widget=forms.PasswordInput())
    role_choices = (('Clinician', 'Clinician'), ('CS', 'Clinical Scientist'), ('Other', 'Other Staff'))
    role = forms.ChoiceField(choices=role_choices)
    hospital = forms.CharField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')
