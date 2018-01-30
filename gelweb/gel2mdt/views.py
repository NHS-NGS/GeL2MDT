from django.shortcuts import render
from .forms import *
from .models import *
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .database_utils import add_cases
from django.contrib import messages
from django.db import IntegrityError
from .tests import test_setup

# Create your views here.
def register(request):
    """ Registration view for all new users
    """
    registered = False
    username = ''

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            first_name = user_form.cleaned_data['first_name']
            last_name = user_form.cleaned_data['last_name']
            username = user_form.cleaned_data['email']
            password = user_form.cleaned_data['password']
            email = user_form.cleaned_data['email']
            role = user_form.cleaned_data['role']
            hospital = user_form.cleaned_data['hospital']
            try:
                user = User(username=username, first_name=first_name, last_name=last_name, password=password,
                            email=email, is_active=False)
                user.save()
                user.set_password(user.password)
                user.save()
                registered = True
                if role == 'CS':
                    cs = ClinicalScientist(name=first_name + ' ' + last_name,
                                           email=email,
                                           hospital=hospital)
                    cs.save()
                elif role == 'Clinician':
                    clinician = Clinician(name=first_name + ' ' + last_name,
                                          email=email,
                                          hospital=hospital)
                    clinician.save()
                elif role == 'Other':
                    other = OtherStaff(name=first_name + ' ' + last_name,
                                       email=email,
                                       hospital=hospital)
                    other.save()
            except IntegrityError as e:
                messages.error(request, 'If you have already registered, '
                                        'please contact Bioinformatics to activate your account')
                return HttpResponseRedirect('/register')

    else:
        user_form = UserForm()

    return render(request, 'registration/registration.html',
                  {'user_form': user_form, 'registered': registered, 'username': username})


def index(request):
    '''
    Gives the user the choice between rare disease and cancer
    :param request:
    :return:
    '''
    # We want this to be a choice between cancer and rare disease
    return render(request, 'gel2mdt/index.html', {})


def cancer_main(request):
    '''
    Shows all the Cancer cases the user has access to and allows easy searching of cases
    :param request:
    :return:
    '''

    return render(request, 'gel2mdt/cancer_main.html', {})


def rare_disease_main(request):
    '''
    Shows all the RD cases the user has access to and allows easy searching of cases
    :param request:
    :return:
    '''
    # test_setup.create_dummy_sample()
    return render(request, 'gel2mdt/rare_disease_main.html', {})

