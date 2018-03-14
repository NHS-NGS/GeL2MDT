from django import forms
from .models import *
from django.contrib.auth.models import User
from django.forms import HiddenInput, Textarea, CheckboxInput

class UserForm(forms.ModelForm):
    """ User registration form
    """
    password = forms.CharField(widget=forms.PasswordInput())
    role_choices = (('Clinician', 'Clinician'),
                    ('Clinical Scientist', 'Clinical Scientist'),
                    ('Other Staff', 'Other Staff'))
    role = forms.ChoiceField(choices=role_choices)
    config_dict = load_config.LoadConfig().load()
    if config_dict['center'] == 'GOSH':
        choices = config_dict['GMC'].split(',')
        gmc_choices = []
        for choice in choices:
            choice = choice.strip(' ')
            gmc_choices.append((choice, choice))
        hospital = forms.ChoiceField(choices=gmc_choices)
    else:
        hospital = forms.CharField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

class ProfileForm(forms.Form):
    role_choices = (('Clinician', 'Clinician'),
                    ('Clinical Scientist', 'Clinical Scientist'),
                    ('Other Staff', 'Other Staff'))
    role = forms.ChoiceField(choices=role_choices)
    #Hospital options from config
    config_dict = load_config.LoadConfig().load()
    if config_dict['center'] == 'GOSH':
        choices = config_dict['GMC'].split(',')
        gmc_choices = []
        for choice in choices:
            choice = choice.strip(' ')
            gmc_choices.append((choice, choice))
        hospital = forms.ChoiceField(choices=gmc_choices)
    else:
        hospital = forms.CharField()

class ProbandForm(forms.ModelForm):
    class Meta:
        model = Proband
        fields = ['episode', 'outcome', 'comment', 'status', 'mdt_status', 'pilot_case', 'case_sent']


class DemogsForm(forms.ModelForm):
    class Meta:
        model = Proband
        fields = ['nhs_number', 'lab_number', 'forename', 'surname', 'date_of_birth', 'sex', 'local_id', 'gmc']



class MdtForm(forms.ModelForm):

    class Meta:
        model = MDT
        fields = ['date_of_mdt', 'status']


class ProbandMDTForm(forms.ModelForm):
    class Meta:
        model = Proband
        fields = ('discussion', 'action', )
        widgets = {
            'discussion': Textarea(attrs={'rows': '3'}),
            'action': Textarea(attrs={'rows': '3'}),
        }

class RareDiseaseMDTForm(forms.ModelForm):
    class Meta:
        model = RareDiseaseReport
        fields = ('contribution_to_phenotype', 'change_med',
                  'clinical_trial', 'requires_validation',
                  'inform_reproductive_choice', 'surgical_option',
                  'add_surveillance_for_relatives',
                  'classification', 'id',)
        widgets = {
                   'id': HiddenInput(),
                   'surgical_option': CheckboxInput(),
                   'change_med': CheckboxInput(),
                   'requires_validation': CheckboxInput(),
                   'add_surveillance_for_relatives': CheckboxInput(),
                   'clinical_trial': CheckboxInput(),
                   'inform_reproductive_choice': CheckboxInput(),
                   }

class AddNewAttendee(forms.Form):
    name = forms.CharField()
    config_dict = load_config.LoadConfig().load()
    if config_dict['center'] == 'GOSH':
        choices = config_dict['GMC'].split(',')
        gmc_choices = []
        for choice in choices:
            choice = choice.strip(' ')
            gmc_choices.append((choice, choice))
        hospital = forms.ChoiceField(choices=gmc_choices)
    else:
        hospital = forms.CharField()
    email = forms.EmailField()
    role = forms.ChoiceField(choices=(('Clinician', 'Clinician'),
                                      ('Clinical Scientist', 'Clinical Scientist'),
                                      ('Other Staff', 'Other Staff')))


class GenomicsEnglandform(forms.Form):
    """ Form for entering genomics england information to render a report to be used by the scientists """

    interpretation_id = forms.IntegerField(label='Interpretation ID')
    # Version number of the interpretation
    ir_version = forms.IntegerField(label='Version')
    report_version = forms.IntegerField(label='Clinical Report Version')


class PanelAppform(forms.Form):
    """ Search field for panel app """
    gene_panel = forms.CharField(max_length=255, label="Gene Panel")
    # Panel version number as a float
    gp_version = forms.FloatField(label="Panel Version")

