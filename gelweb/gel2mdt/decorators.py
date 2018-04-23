from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import render, redirect

def sample_permission(function):
    def wrap(request, *args, **kwargs):
        print(function, args, kwargs)
        user_group = request.user.groups.values_list('name', flat=True)
        if 'clinician' in user_group:
            return function(request, *args, **kwargs)
        else:
            return PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def user_is_clinician(url=None):
    """
    Decorator for views that checks that the user has record of being clinician in user groups.
    Redirects to clinicians equivalent page if true
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrap(request, *args, **kwargs):
            user_group = request.user.groups.values_list('name', flat=True)
            if 'clinicians' in user_group:
                if 'report_id' in kwargs:
                    return redirect(f'gel2clin:{url}', kwargs['report_id'])
                else:
                    return redirect(f'gel2clin:{url}')
            else:
                return view_func(request, *args, **kwargs)

        wrap.__doc__ = view_func.__doc__
        wrap.__name__ = view_func.__name__
        return wrap
    return decorator

