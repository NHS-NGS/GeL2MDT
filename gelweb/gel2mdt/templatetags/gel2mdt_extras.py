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
import os
import subprocess

from django import template
from gel2mdt.config import load_config


register = template.Library()
config = load_config.LoadConfig().load()

def is_git_repo():
    if subprocess.call(["git", "branch"], stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w')) != 0:
        return False
    else:
        return True

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def count_dict(dictionary):
    return len(dictionary.keys())


@register.filter
def sort_by(queryset, order):
    return queryset.order_by(order)


@register.filter
def has_group_permission(user, argument):
    if user.groups.all():
        for group in user.groups.all():
            if hasattr(group, 'grouppermissions'):
                group_permission = group.grouppermissions
                if getattr(group_permission, argument):
                    return True
    return False


@register.simple_tag
def version_number():
    if not is_git_repo():
        return config["VERSION_NUMBER"]
    version_fetch_cmd = "git tag | sort -V | tail -1"
    version_fetch_process = subprocess.Popen(
            version_fetch_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
    )
    version_fetch_out, version_fetch_err = version_fetch_process.communicate()
    version = str(version_fetch_out, "utf-8")

    return version

@register.simple_tag
def build():
    if not is_git_repo():
        return ''
    build_fetch_cmd = "git log -1 --stat"
    build_fetch_process = subprocess.Popen(
            build_fetch_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
    )
    build_fetch_out, build_fetch_err = build_fetch_process.communicate()
    build_fetch = str(build_fetch_out, "utf-8").split(' ')

    build_hash = build_fetch[1][:6]
    return 'build ' + build_hash
