from django.shortcuts import render
from .forms import *
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

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
            user = User(username=username, first_name=first_name, last_name=last_name, password=password,
                        email=email, is_active=False)
            user.save()
            user.set_password(user.password)
            user.save()
            registered = True

    else:
        user_form = UserForm()

    return render(request, 'registration/registration.html',
                  {'user_form': user_form, 'registered': registered, 'username': username})

def index(request):
    return render(request, 'gel2mdt/index.html', {} )
