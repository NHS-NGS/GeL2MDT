from django import forms
from .models import *
from django.contrib.auth.models import User
from django.forms import HiddenInput, Textarea, CheckboxInput
from django.forms import BaseFormSet


class UserForm(forms.ModelForm):
    """
    User registration form
    """
    password = forms.CharField(widget=forms.PasswordInput())
    role_choices = (('Clinician', 'Clinician'),
                    ('Clinical Scientist', 'Clinical Scientist'),
                    ('Other Staff', 'Other Staff'))
    role = forms.ChoiceField(choices=role_choices)
    config_dict = load_config.LoadConfig().load()
    if config_dict['GMC'] != 'None':
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
    """
    Allows users to change their info.
    TODO - Remove this as could be security risk if 2 permission layers are introduced
    """
    role_choices = (('Clinician', 'Clinician'),
                    ('Clinical Scientist', 'Clinical Scientist'),
                    ('Other Staff', 'Other Staff'),
                    ('Unknown', 'Unknown'),)
    role = forms.ChoiceField(choices=role_choices)
    config_dict = load_config.LoadConfig().load()
    if config_dict['GMC'] != 'None':
        choices = config_dict['GMC'].split(',')
        gmc_choices = []
        for choice in choices:
            choice = choice.strip(' ')
            gmc_choices.append((choice, choice))
        hospital = forms.ChoiceField(choices=gmc_choices)
    else:
        hospital = forms.CharField()


class ProbandForm(forms.ModelForm):
    '''
    Form used for allowing users edit proband information
    '''
    class Meta:
        model = Proband
        fields = ['episode', 'outcome', 'comment', 'status', 'mdt_status', 'pilot_case', 'case_sent']


class RelativeForm(forms.ModelForm):
    '''
    Form used for allowing users edit Relative demographics
    '''
    class Meta:
        model = Relative
        fields = ['forename', 'surname', 'date_of_birth', 'nhs_number',
                  'sex', 'affected_status']


class DemogsForm(forms.ModelForm):
    '''
    Form used for allowing users edit proband demographics
    '''
    class Meta:
        model = Proband
        fields = ['nhs_number', 'lab_number', 'forename', 'surname', 'date_of_birth', 'sex', 'local_id', 'gmc']


class PanelForm(forms.Form):
    '''
    Form used for allowing users to add a panel to a proband
    '''
    panel = forms.ModelChoiceField(queryset=PanelVersion.objects.order_by('panel'))


class ClinicianForm(forms.Form):
    '''
    Form used for allowing users to change a probands clinician
    '''
    clinician = forms.ModelChoiceField(queryset=Clinician.objects.filter(added_by_user=True).order_by('name'))


class AddClinicianForm(forms.ModelForm):
    '''
    Form used in Proband View to allow users add a new Clinician
    '''
    config_dict = load_config.LoadConfig().load()
    if config_dict['GMC'] != 'None':
        choices = config_dict['GMC'].split(',')
        gmc_choices = []
        for choice in choices:
            choice = choice.strip(' ')
            gmc_choices.append((choice, choice))
        hospital = forms.ChoiceField(choices=gmc_choices)
    else:
        hospital = forms.CharField()

    class Meta:
        model = Clinician
        fields = ['name', 'hospital', 'email']


class CaseAssignForm(forms.ModelForm):
    '''
    Form for specifying which user a case is assigned to
    '''
    class Meta:
        model = GELInterpretationReport
        fields = ["assigned_user"]


class MdtForm(forms.ModelForm):
    '''
    Form which edits MDT instance specific fields such as date and status
    '''
    class Meta:
        model = MDT
        fields = ['description', 'date_of_mdt', 'status']


class ProbandMDTForm(forms.ModelForm):
    '''
    Form used in Proband View at MDT which allows users to fill in proband textfields
    '''
    class Meta:
        model = Proband
        fields = ('discussion', 'action', 'status')
        widgets = {
            'discussion': Textarea(attrs={'rows': '3'}),
            'action': Textarea(attrs={'rows': '3'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProbandMDTForm, self).__init__(*args, **kwargs)
        self.fields['status'].required = False


class RareDiseaseMDTForm(forms.ModelForm):
    '''
    Form used in Proband View at MDT which allows users to fill in exit questionaire questions
    '''
    class Meta:
        model = RareDiseaseReport
        fields = ('contribution_to_phenotype', 'change_med',
                  'clinical_trial',
                  'inform_reproductive_choice', 'surgical_option',
                  'add_surveillance_for_relatives',
                  'classification', 'id',)
        widgets = {
                   'id': HiddenInput(),
                   'surgical_option': CheckboxInput(),
                   'change_med': CheckboxInput(),
                   'add_surveillance_for_relatives': CheckboxInput(),
                   'clinical_trial': CheckboxInput(),
                   'inform_reproductive_choice': CheckboxInput(),
                   }


class AddNewAttendee(forms.Form):
    '''
    Form for allowing users to add new attendee which would then  be inserted into CS, Clinician or OtherStaff table
    '''
    name = forms.CharField()
    config_dict = load_config.LoadConfig().load()
    if config_dict['GMC'] != 'None':
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


class AddVariantForm(forms.ModelForm):
    '''
    Allows users to add a variant to a report. Users have to enter
    chromosome, position, reference, alternate, dbsnp
    TODO should check everything users enters for consistancy
    '''
    def clean_reference(self):
        data = self.cleaned_data['reference'].strip()
        if not all([f in ['A', 'T', 'G', 'C'] for f in data]):
            raise forms.ValidationError("Not DNA sequence")
        else:
            return data

    def clean_alternate(self):
        data = self.cleaned_data['alternate'].strip()
        if not all([f in ['A', 'T', 'G', 'C'] for f in data]):
            raise forms.ValidationError("Not DNA sequence")
        else:
            return data

    class Meta:
        model = Variant
        fields = ['chromosome',
                  'position',
                  'reference',
                  'alternate',
                  'db_snp_id']
        widgets = {'reference': Textarea(attrs={'rows': '2'}),
                   'alternate': Textarea(attrs={'rows': '2'})}


class GenomicsEnglandform(forms.Form):
    """ Form for entering genomics england information to render a report to be used by the scientists """

    interpretation_id = forms.IntegerField(label='Interpretation ID')
    # Version number of the interpretation
    ir_version = forms.IntegerField(label='Version')
    report_version = forms.IntegerField(label='Clinical Report Version')
