from functools import wraps
from django.shortcuts import render, redirect
from .models import Clinician

def user_is_clinician(url=None):
    """
    Decorator for views that checks that the user is a clinician. Redirects to clinicians equivalent page if true.
    Exception if user is listed as staff. Otherwise will provide original request.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrap(request, *args, **kwargs):
            clinicians_emails = Clinician.objects.all().values_list('email', flat=True)
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)
            elif request.user.email not in clinicians_emails:
                return view_func(request, *args, **kwargs)
            else:
                if 'report_id' in kwargs:
                    return redirect(f'gel2clin:{url}', kwargs['report_id'])
                else:
                    return redirect(f'gel2clin:{url}')

        wrap.__doc__ = view_func.__doc__
        wrap.__name__ = view_func.__name__
        return wrap
    return decorator

