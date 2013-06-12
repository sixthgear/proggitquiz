from django.core.urlresolvers import reverse

class Button(object):
    def __init__(self, challenge, set, sol):
        self.set = set
        self.sol = sol 
        self.icon = 'icon-time'
        self.action = '',
        self.classes = ('', '')
        self.time = '0:00'
        self.running = False
        self.disabled = False
        self.url = ''

class LoginButton(Button):
    """
    not-logged-in button
    """
    def __init__(self, challenge, *args, **kwargs):
        super(LoginButton, self).__init__(challenge, *args, **kwargs)
        self.action = 'Login to participate'
        self.time = self.set.get_time_limit()
        self.disabled = True
        

class LockedButton(Button):
    """
    locked set button
    """
    def __init__(self, challenge, *args, **kwargs):
        super(LockedButton, self).__init__(challenge, *args, **kwargs)
        self.action = 'Complete previous set to unlock'
        self.time = self.set.get_time_limit()
        self.disabled = True
        
        
class CompletedButton(Button):
    """
    completed set button
    """
    def __init__(self, challenge, *args, **kwargs):
        super(CompletedButton, self).__init__(challenge, *args, **kwargs)        
        self.action = 'Completed!'
        self.classes = ('btn-success', 'btn-success')
        self.icon = 'icon-ok icon-white'

class ExpiredButton(Button):
    """
    expired set button
    """
    def __init__(self, challenge, *args, **kwargs):
        super(ExpiredButton, self).__init__(challenge, *args, **kwargs)
        self.action = 'Retry %s set' % self.set.title.lower()
        self.classes = ('btn-info btn-refresh', 'btn-inverse')
        self.icon = 'icon-time icon-white'
        self.time = self.set.get_time_limit()
        self.url = reverse('pq.views.solution_begin', args=[challenge.id, self.set.id])
    

class RunningButton(Button):
    """
    in-progress set button
    """
    def __init__(self, challenge, *args, **kwargs):    
        super(RunningButton, self).__init__(challenge, *args, **kwargs)
        self.action = '%s set in progress' % self.set.title
        self.classes = ('btn-primary', 'btn-inverse timer-running')
        self.icon = 'icon-time icon-white'
        self.time = self.sol.get_time_left()
        self.running = True
        self.url = reverse('pq.views.solution_begin', args=[challenge.id, self.set.id])
    

class RunningUnlimitedButton(RunningButton):
    """
    in-progress set with no time limit button
    """
    def __init__(self, challenge, *args, **kwargs):
        super(RunningUnlimitedButton, self).__init__(challenge, *args, **kwargs)
        self.classes = ('btn-primary', 'btn-inverse')        
        self.time = '0:00'
        
class OpenButton(Button):
    """
    open set button          
    """
    def __init__(self, challenge, *args, **kwargs):
        super(OpenButton, self).__init__(challenge, *args, **kwargs)
        self.action = 'Download input'
        self.classes = ('btn-info btn-refresh', 'btn-inverse')
        self.icon = 'icon-time icon-white'
        self.time = self.set.get_time_limit()
        self.url = reverse('pq.views.solution_begin', args=[challenge.id, self.set.id])
    