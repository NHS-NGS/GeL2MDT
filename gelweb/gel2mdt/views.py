from django.shortcuts import render
from .forms import *
from .models import *
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .database_utils import add_cases
from django.contrib import messages
from django.db import IntegrityError

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
            try:
                user = User(username=username, first_name=first_name, last_name=last_name, password=password,
                            email=email, is_active=False)
                user.save()
                user.set_password(user.password)
                user.save()
                registered = True
                if role == 'CS':
                    cs = ClinicalScientist(cs_name=first_name + ' ' + last_name,
                                           email=email)
                    cs.save()
                elif role == 'Clinician':
                    clinician = Clinician(clinician_name=first_name + ' ' + last_name,
                                          hospital='test',
                                          email=email)
                    clinician.save()
                elif role == 'Other':
                    other = OtherStaff(staff_name=first_name + ' ' + last_name,
                                       email=email)
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
    # m = add_cases.InterpretationList()
    # print(m.all_cases_count)
    return render(request, 'gel2mdt/index.html', {} )
