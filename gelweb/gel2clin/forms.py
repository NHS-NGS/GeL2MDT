from django import forms
from gel2mdt.models import *
from django.forms import HiddenInput, Textarea, CheckboxInput

class ProbandCancerForm(forms.ModelForm):
    '''
    Form used for allowing users edit proband information
    '''
    class Meta:
        model = Proband
        fields = ['recruiting_disease', 'disease_subtype',
                  'disease_stage', 'disease_grade', 'deceased',
                  'previous_treatment', 'currently_in_clinical_trial',
                  'current_clinical_trial_info', 'suitable_for_clinical_trial',
                  'previous_testing']

