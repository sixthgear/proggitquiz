"""
Set of templatetags relating to challenges.
"""
# from pygments import highlight
# from pygments.lexers import *
# from pygments.formatters import HtmlFormatter

from django.db.models import Sum, Max
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from pq.models import Problem
from itertools import chain

register = template.Library()

@register.inclusion_tag('current_challenges.html', takes_context=True)
def current_challenges(context, size=0):
    request = context['request']
    scoreboard = {}

    if size == 0:
        problems = Problem.objects.filter(status__gte=2).order_by('-started')
    else:
        problems = Problem.objects.filter(status=2).order_by('-started')

    if request.user.is_authenticated():        
        scores = problems.filter(solution__author=request.user, solution__status=2)
        scores_a = scores.annotate(score=Sum('solution__set__points')).order_by('id')
        scores_b = scores.annotate(score=Sum('solution__bonuses__points')).order_by('id')
        
        for sa, sb in zip(scores_a, scores_b):
            scoreboard[sa.id] = sa.score
            if sb.score:
                scoreboard[sa.id] += sb.score                
    
    for p in problems:
            p.score = scoreboard.get(p.id, 0)

    return {"problems": problems, "size": size}

@register.simple_tag
def get(value, arg, offset):
    try:
        return value[int(arg) + offset][0]
    except:
        return None