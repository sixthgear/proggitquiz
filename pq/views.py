import os
import itertools
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Sum, Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import timezone
from pq.models import Problem, Solution, Bonus, Set
from pq.forms import SolutionForm        

def home(request):
    """
    Homepage.
    """    
    # messages.add_message(request, messages.INFO, 'Welcome to proggitquiz, %s!' % request.user)
    return render_to_response('home.html', {'slug': 'home'}, RequestContext(request))

def challenge_list(request):
    """
    List of all challenges.
    TODO: pagination
    """
    
    context = {'slug': 'challenges'}
    return render_to_response('challenge_list.html', context, RequestContext(request))

def get_scoreboard(problem, solution, username=None):
    # calculate scoreboard    
    sb_users = User.objects.filter(solution__problem=problem, solution__status=2)
    scoreboard = sb_users.annotate(score=Sum('solution__set__points')).order_by('id')
    scoreboard_b = sb_users.annotate(score=Sum('solution__bonuses__points')).order_by('id')
    for sa, sb in zip(scoreboard, scoreboard_b):
        if sb.score:
            sa.score += sb.score        
        sa.solutions = sa.solution_set.filter(problem=problem, status=2)

    scoreboard = sorted(list(scoreboard), key=lambda x: x.score, reverse=True)
    return scoreboard

def challenge(request, problem=None):    
    """
    View details of a single challenge.
    """
    min_status = 1 if request.user.is_superuser else 2
    problem = get_object_or_404(Problem, id=problem, status__gte=min_status)
    sets = problem.sets.all()
    buttons = []

    if request.user.is_authenticated():
        solutions = problem.solution_set.filter(author=request.user).order_by('set')
        max_set = solutions.filter(status=2).aggregate(Max('set'))['set__max'] or 0
    else:
        solutions = []
        max_set = 0

    for set in sets:
        set.open = False
    for set in sets:
        set.open = True
        if set.id > max_set:
            break                    

    for set, sol in itertools.izip_longest(sets, solutions):
        b = {'set': set, 'sol': sol, 'icon': 'icon-time'}
        if not request.user.is_authenticated():
            b.update({
                'action': 'Login to participate', 
                'time': set.get_time_limit(),
                'disabled': True                
            })
        elif not sol and not set.open:
            # and set != sets[0]:
            b.update({
                'action': 'Complete previous set to unlock',                
                # 'action': 'Complete %s set to unlock' % sets[set.id-2].title, 
                'time': set.get_time_limit(),
                'disabled': True
            })
        elif sol and sol.status == 2:            
            b.update({
                'action': 'Completed!',
                'class': ('btn-success', 'btn-success'),
                'icon': 'icon-ok icon-white'
            })
        elif sol and sol.is_expired():
            b.update({
                'action': 'Retry %s set' % set.title.lower(), 
                'class': ('btn-info btn-refresh', 'btn-inverse'),
                'icon': 'icon-time icon-white',
                'time': set.get_time_limit(),
                'url': reverse('pq.views.solution_begin', args=[problem.id, set.id]),
            })
        elif sol and set.time_limit > 0:
            running_solution = sol
            b.update({
                'action': '%s set in progress' % set.title,
                'class': ('btn-primary', 'btn-inverse timer-running'),
                'icon': 'icon-time icon-white',
                'time': sol.get_time_left(),
                'running': True,
                'url': reverse('pq.views.solution_begin', args=[problem.id, set.id])
            })
        elif sol:
            # running solution with no time limit
            running_solution = sol
            b.update({
                'action': '%s set in progress' % set.title,
                'class': ('btn-primary', 'btn-inverse'),
                'icon': 'icon-time icon-white',
                'time': '0:00',
                'running': True,
                'url': reverse('pq.views.solution_begin', args=[problem.id, set.id])
            })            
        else:
            b.update({
                'action': 'Download input', 
                'class': ('btn-info btn-refresh', 'btn-inverse'),
                'icon': 'icon-time icon-white',
                'time': set.get_time_limit(),
                'url': reverse('pq.views.solution_begin', args=[problem.id, set.id])
            })
        buttons.append(b)

    scoreboard = get_scoreboard(problem, solution)
    if request.user in scoreboard:
        my_score = [x.score for x in scoreboard if x==request.user][0]
    else:
        my_score = 0
    
    context = {
        'slug': 'challenges',
        'problem': problem,
        'buttons': buttons,
        # 'solutions': problem.solution_set.filter(status=2),
        'bonuses': problem.bonuses.all(),
        's_form': SolutionForm(),
        'scoreboard': scoreboard,
        'my_score': my_score,
    }

    if not problem.source_req:
        context['s_form'].fields.pop('source')

    return render_to_response('challenge.html', context, RequestContext(request))

@login_required
def solution_begin(request, problem, set):
    """
    Begin a solution
    """
    problem = get_object_or_404(Problem, id=problem)
    problem_sets = problem.sets.all()
    n_completed = problem.solution_set.filter(author=request.user, status=2).count()
    next_set = None
    output = ''

    if n_completed < problem_sets.count():
        next_set = problem_sets[n_completed]
    
    if not next_set:
        messages.add_message(request, messages.ERROR, 'You may not begin this challenge yet.')
        return HttpResponseRedirect(reverse('pq.views.challenge', args=[problem.id]))

    solutions = problem.solution_set.filter(author=request.user, set=set)

    if not solutions:
        solution = Solution()
        solution.author = request.user
        solution.problem = problem
        solution.set_id = int(set)       
        output = solution.generate() # generate new input
        solution.save()
    else:
        solution = solutions[0]
        if solution.is_expired():            
            output = solution.generate() # generate new input
            solution.save()            
        
    filename = 'pq-p%d-%s-%d.in' % (
        problem.id,
        solution.set.title.lower(),
        solution.attempt
    )

    response = HttpResponse(output, mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

@login_required
def solution_upload(request, problem, solution):
    """
    Upload and verify a solution
    """
    problem = get_object_or_404(Problem, id=problem)
    solution = get_object_or_404(Solution, id=solution)
    
    if problem.status != 2:
        return HttpResponseRedirect(reverse('pq.views.challenge_list'))

    if solution.is_expired():
        return HttpResponseRedirect(reverse('pq.views.challenge', args=[problem.id]))

    if request.POST:
        form = SolutionForm(request.POST, request.FILES, instance=solution)
        if form.is_valid():
            # valid and complete!
            solution.status = 2
            solution.submitted = datetime.now()
            solution.apply_bonuses()
            solution.save()
        else:
            for e in form.non_field_errors():
                messages.add_message(request, messages.ERROR, e)
            
    return HttpResponseRedirect(reverse('pq.views.challenge', args=[problem.id]))
    
def solution(request, problem, solution):
    """
    View details of a single solution.
    """
    problem = get_object_or_404(Problem, id=problem)
    solution = get_object_or_404(Solution, id=solution, problem=problem)

    if not problem.source_req:
        return HttpResponseRedirect(reverse('pq.views.challenge', args=[problem.id]))    
    # solutions = problem.solution_set.order_by('id')

    context = {
        'slug': 'challenges',
        'problem': problem,
        'solution': solution,
        # 'buttons': buttons,
        # 'solutions': problem.solution_set.filter(status=2),
        # 'bonuses': Bonus.objects.all(),
        # 's_form': SolutionForm(),
        'scoreboard': get_scoreboard(problem, solution), 
        # 'my_score': my_score,        
    }

    return render_to_response('solution.html', context, RequestContext(request))
    
def solution_raw(request, problem, solution):
    """
    View details of a single solution.
    """
    problem = get_object_or_404(Problem, id=problem)
    solution = get_object_or_404(Solution, id=solution, problem=problem)
    response = HttpResponse(solution.source, mimetype='text/plain')
    return response

def solution_download(request, problem, solution):
    """
    View details of a single solution.
    """    
    problem = get_object_or_404(Problem, id=problem)
    solution = get_object_or_404(Solution, id=solution, problem=problem)    
    response = HttpResponse(solution.source, mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(solution.source.name)
    return response
    
def solution_delete(request, problem, solution):
    problem = get_object_or_404(Problem, id=problem)
    solution = get_object_or_404(Solution, id=solution, problem=problem)
    if request.user != solution.author:
        messages.add_message(request, messages.INFO, 'Hey, you\'re not allowed to delete that.')
        return HttpResponseRedirect(reverse('apps.challenges.views.solution', args=[problem.id, solution.id]))
    solution.delete()
    messages.add_message(request, messages.INFO, 'Deleted.')
    return HttpResponseRedirect(reverse('apps.challenges.views.challenge', args=[problem.id]))

def rules(request):
    """
    Rule info page.
    """
    return render_to_response('rules.html', {'slug': 'rules'}, RequestContext(request))
    
def contribute(request):
    """
    Contribute page.
    """
    return render_to_response('contribute.html', {'slug': 'contribute'}, RequestContext(request))

def user_profile(request, username=None):
    """
    User profile
    """
    if not username:
        user = request.user
        username = request.user.username
    else:
        print username
        user = get_object_or_404(User, username=username)

    # messages.add_message(request, messages.INFO, 'Welcome to proggitquiz, %s.' % username)
    return HttpResponseRedirect(reverse('pq.views.home'))
