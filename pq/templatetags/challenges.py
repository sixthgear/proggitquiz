"""
Set of templatetags relating to challenges.
"""
# from pygments import highlight
# from pygments.lexers import *
# from pygments.formatters import HtmlFormatter

from django import template
from django.template.defaultfilters import stringfilter

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from pq.models import Problem

register = template.Library()

@register.inclusion_tag('current_challenges.html')
def current_challenges(size=0):
    if size == 0:
        problems = Problem.objects.filter(status__gte=2).order_by('started')
    else:
        problems = Problem.objects.filter(status=2).order_by('started')

    context = {"problems": problems, "size": size}
    return context

@register.simple_tag
def get(value, arg, offset):
    try:
        return value[int(arg) + offset][0]
    except:
        return None

# @register.filter
# @stringfilter
# def code(value, arg=''):
#     try:
#         lexer = get_lexer_by_name(arg.lower())
#     except:
#         try:
#             lexer = guess_lexer(value)
#         except:
#             lexer = PythonLexer()            
#     return mark_safe(highlight(value,lexer,HtmlFormatter(linenos='table')))
