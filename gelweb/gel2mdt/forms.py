"""Copyright (c) 2018 Great Ormond Street Hospital for Children NHS Foundation
Trust & Birmingham Women's and Children's NHS Foundation Trust

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from datetime import datetime

from django import forms
from django.contrib.auth.models import User
from django.forms import HiddenInput, Textarea, CheckboxInput, Select, ModelChoiceField
from django.forms import BaseFormSet

from .models import *


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
    role = forms.ChoiceField(choices=role_choices, required=False)
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
        fields = ['outcome', 'comment']
        widgets = {
            'outcome': Textarea(attrs={'rows': '3'}),
            'comment': Textarea(attrs={'rows': '3'}),
        }


class VariantValidationForm(forms.ModelForm):
    """
    Form used to change values used for variant validation tracking.
    """
    def __init__(self, *args, **kwargs):
        super(VariantValidationForm, self).__init__(*args, **kwargs)
        self.fields['validation_responsible_user'].required=False

    class Meta:
        model = ProbandVariant
        fields = [
            'validation_status',
            'validation_responsible_user',
        ]


class AddCommentForm(forms.ModelForm):
    '''
    Adds a new CaseComment in the Proband page
    '''
    class Meta:
        model = CaseComment
        fields = ['comment']


class GELIRForm(forms.ModelForm):
    '''
    Form used for allowing users edit proband information
    '''
    class Meta:
        model = GELInterpretationReport
        fields = ['case_status', 'mdt_status', 'pilot_case', 'case_sent', 'no_primary_findings', 'case_code']

    def save(self):
        gelir = self.instance
        data = self.cleaned_data
        gelir.case_status = data['case_status']
        gelir.mdt_status = data['mdt_status']
        gelir.pilot_case = data['pilot_case']
        gelir.case_sent = data['case_sent']
        gelir.no_primary_findings = data['no_primary_findings']
        gelir.case_code = data['case_code']
        gelir.save(overwrite=True)


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


class UserChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)


class CaseAssignForm(forms.ModelForm):
    '''
    Form for specifying which user a case is assigned to
    '''
    assigned_user = UserChoiceField(queryset=User.objects.all().order_by('first_name'))

    class Meta:
        model = GELInterpretationReport
        fields = ["assigned_user"]

    def save(self):
        gelir = self.instance
        data = self.cleaned_data
        gelir.assigned_user = data['assigned_user']
        gelir.save(overwrite=True)

class FirstCheckAssignForm(forms.ModelForm):
    '''
    Form for specifying which user performed the first check
    '''
    first_check = UserChoiceField(queryset=User.objects.all().order_by('first_name'))

    class Meta:
        model = GELInterpretationReport
        fields = ["first_check"]

    def save(self):
        gelir = self.instance
        data = self.cleaned_data
        gelir.first_check = data['first_check']
        gelir.save(overwrite=True)

class SecondCheckAssignForm(forms.ModelForm):
    '''
    Form for specifying which user performed the second check
    '''
    second_check = UserChoiceField(queryset=User.objects.all().order_by('first_name'))

    class Meta:
        model = GELInterpretationReport
        fields = ["second_check"]

    def save(self):
        gelir = self.instance
        data = self.cleaned_data
        gelir.second_check = data['second_check']
        gelir.save(overwrite=True)


class MdtForm(forms.ModelForm):
    '''
    Form which edits MDT instance specific fields such as date and status
    '''
    class Meta:
        model = MDT
        fields = ['description', 'date_of_mdt', 'status', 'sent_to_clinician']

class MdtSentToClinicianForm(forms.ModelForm):
    '''
    Form for recording the whether the MDT list has been sent to the clinician
    '''
    class Meta:
        model = MDT
        fields = ['sent_to_clinician']

    def __init__(self, *args, **kwargs):
        super(MdtSentToClinicianForm, self).__init__(*args, **kwargs)
        self.fields['sent_to_clinician'].required = False


class ProbandMDTForm(forms.ModelForm):
    '''
    Form used in Proband View at MDT which allows users to fill in proband textfields
    '''
    class Meta:
        model = Proband
        fields = ('discussion', 'action')
        widgets = {
            'discussion': Textarea(attrs={'rows': '3'}),
            'action': Textarea(attrs={'rows': '3'}),
        }


class GELIRMDTForm(forms.ModelForm):
    '''
    Form used in Proband View at MDT which allows users to fill in proband textfields
    '''

    class Meta:
        model = GELInterpretationReport
        fields = ('case_status',)

    def __init__(self, *args, **kwargs):
        super(GELIRMDTForm, self).__init__(*args, **kwargs)
        self.fields['case_status'].required = False

    def save(self):
        gelir = self.instance
        data = self.cleaned_data
        gelir.case_status = data['case_status']
        gelir.save(overwrite=True)


class RareDiseaseMDTForm(forms.ModelForm):
    '''
    Form used in Proband View at MDT which allows users to fill in exit questionaire questions
    '''
    requires_validation = forms.ChoiceField(
        choices=(
            ('U', 'Unknown'),
            ('A', 'Awaiting Validation'),
            ('K', 'Urgent Validation'),
            ('I', 'In Progress'),
            ('P', 'Passed Validation'),
            ('F', 'Failed Validation'),
            ('N', 'Not Required'),
        )
    )

    class Meta:
        model = RareDiseaseReport
        fields = (
            'contribution_to_phenotype', 'change_med',
            'clinical_trial', 'requires_validation',
            'discussion', 'action',
            'inform_reproductive_choice', 'surgical_option',
            'add_surveillance_for_relatives',
            'classification', 'id',)
        widgets = {
            'id': HiddenInput(),
            'surgical_option': CheckboxInput(),
            'requires_validation': Select(),
            'change_med': CheckboxInput(),
            'add_surveillance_for_relatives': CheckboxInput(),
            'clinical_trial': CheckboxInput(),
            'inform_reproductive_choice': CheckboxInput(),
            'discussion': Textarea(attrs={'rows': '4'}),
            'action': Textarea(attrs={'rows': '4'})
        }

    def save(self, commit=True):
        selected_validation_status = self.cleaned_data['requires_validation']
        pv = self.instance.proband_variant

        pv.validation_status = selected_validation_status
        if not pv.validation_datetime_set:
            pv.validation_datetime_set = datetime.now()

        pv.save()

        return super(RareDiseaseMDTForm, self).save(commit=commit)


class CancerMDTForm(forms.ModelForm):
    '''
    Form used in Proband View at MDT which allows users to fill in exit questionaire questions
    '''
    requires_validation = forms.ChoiceField(
        choices=(
            ('U', 'Unknown'),
            ('A', 'Awaiting Validation'),
            ('K', 'Urgent Validation'),
            ('I', 'In Progress'),
            ('P', 'Passed Validation'),
            ('F', 'Failed Validation'),
            ('N', 'Not Required'),
        )
    )

    class Meta:
        model = CancerReport
        fields = ('variant_use', 'action_type', 'validated',
                  'validated_assay_type',
                  'classification', 'id',)
        widgets = {'id': HiddenInput(),
                   'validated': CheckboxInput(),
                   }

    def save(self, commit=True):
        selected_validation_status = self.cleaned_data['requires_validation']
        pv = self.instance.proband_variant

        pv.validation_status = selected_validation_status
        if not pv.validation_datetime_set:
            pv.validation_datetime_set = datetime.now()

        pv.save()

        return super(CancerMDTForm, self).save(commit=commit)


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


class GeneSearchForm(forms.Form):
    gene = forms.CharField(max_length=25, widget = forms.TextInput(attrs={'style': 'width:200px'}))


class AddCaseAlert(forms.ModelForm):

    def clean_gel_id(self):
        if self.cleaned_data['gel_id'].isdigit() and len(self.cleaned_data['gel_id']) >= 8:
            return self.cleaned_data['gel_id'].strip()
        else:
            forms.ValidationError("Doesn't look like a GELID")


    class Meta:
        model = CaseAlert
        fields = ['gel_id', 'comment', 'sample_type']
