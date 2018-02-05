from django import forms
from .models import *
from django.contrib.auth.models import User
from django.forms import HiddenInput, Textarea, CheckboxInput
import time

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


class ProbandForm(forms.ModelForm):
    class Meta:
        model = Proband
        fields = ['episode', 'outcome', 'comment', 'status', 'mdt_status', 'pilot_case', 'case_sent']


class MdtForm(forms.ModelForm):

    class Meta:
        model = MDT
        fields = ['date_of_mdt', 'status']

class ProbandMDTForm(forms.ModelForm):
    class Meta:
        model = Proband
        fields = ['discussion', 'action', 'id']
        widgets = {
            'id': HiddenInput(),
            'discussion': Textarea(attrs={'rows': '3'}),
            'action': Textarea(attrs={'rows': '3'}),
        }

class VariantMDTForm(forms.ModelForm):
    class Meta:
        model = ProbandVariant
        fields = ('contribution_to_phenotype', 'change_med',
                  'action', 'discussion', 'clinical_trial',
                  'inform_reproductive_choice', 'surgical_option',
                  'add_surveillance_for_relatives',
                  'classification', 'id',)
        widgets = {'id': HiddenInput(),
                   'action': Textarea(attrs={'rows': 4, 'cols': 30}),
                   'discussion': Textarea(attrs={'rows': 4, 'cols': 30}),
                   'surgical_option': CheckboxInput(),
                   'change_med': CheckboxInput(),
                   'add_surveillance_for_relatives': CheckboxInput(),
                   'clinical_trial': CheckboxInput(),
                   'inform_reproductive_choice': CheckboxInput(),
                   }
