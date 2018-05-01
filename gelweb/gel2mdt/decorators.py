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
