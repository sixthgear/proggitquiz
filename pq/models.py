import os
import re
from datetime import datetime, timedelta
from subprocess import check_output, Popen, PIPE
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Max

PRB_STATUS_CHOICES = (
    (0, 'Removed'),
    (1, 'Draft'),
    (2, 'In Progress'),
    (3, 'Archived'),    
)

CHALLENGE_TYPE_CHOICES = (
    (0, 'Default'),
    (1, 'Hex Grid'),     
)

SOL_STATUS_CHOICES = (
    (0, 'Incomplete'),
    (1, 'Expired'),
    (2, 'Complete'),
)

GRACE_PERIOD = 5 # seconds

def get_fn_generator(instance, filename):    
    slug = re.sub(r'[\W_]+', '', instance.title.lower())[:50]
    return 'generators/%s-gen.py' % slug

def get_fn_validator(instance, filename):
    slug = re.sub(r'[\W_]+', '', instance.title.lower())[:50]
    return 'validators/%s-val.py' % slug

def get_fn_output(instance, filename):
    fn, ext = os.path.splitext(filename)
    return 'output/p%03d-%d-%s.out' % (
        instance.challenge.id, 
        instance.author.id, 
        instance.set.title.lower()[:3])

def get_fn_source(instance, filename):
    fn, ext = os.path.splitext(filename)
    return 'source/p%03d-%s-%s%s' % (
        instance.challenge.id, 
        instance.author.username, 
        instance.set.title.lower()[:3], 
        ext)

class Challenge(models.Model):
    """
    A challenge is a single problem split into multiple sets. It may be part of a themed set of challenges.
    """

    # basic info
    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    status = models.IntegerField(choices=PRB_STATUS_CHOICES)

    # rules
    type = models.IntegerField(choices=CHALLENGE_TYPE_CHOICES, default=0)
    source_req = models.BooleanField('Source code required?')
    use_input_validation = models.BooleanField('Input validates output?')
    # spoilers = models.BooleanField()    

    # descriptions
    preamble = models.TextField()
    body = models.TextField()

    # scripts
    generator = models.FileField(null=True, upload_to=get_fn_generator)
    validator = models.FileField(null=True, upload_to=get_fn_validator)    
    
    # dates
    created = models.DateField(auto_now_add=True)
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)

    # sets and bonuses
    sets = models.ManyToManyField('Set', blank=True)
    bonuses = models.ManyToManyField('Bonus', blank=True)

    def __unicode__(self):
        return self.title


class Set(models.Model):
    """
    Sets are reusable problem difficulty classes.
    """

    title = models.CharField(max_length=100)
    points = models.IntegerField()
    time_limit = models.IntegerField(help_text='Time limit in seconds.')

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.get_time_limit())

    def get_time_limit(self):
        minute = int(self.time_limit / 60)
        second = int(self.time_limit % 60)
        return "%d:%02d" % (minute, second)        

class Solution(models.Model):
    """
    A solution is a user attempt to solve a set.
    """

    challenge = models.ForeignKey('Challenge')
    author = models.ForeignKey(User)    
    set = models.ForeignKey(Set, default=0)

    status = models.IntegerField(choices=SOL_STATUS_CHOICES, default=0)
    attempt = models.IntegerField(default=0)
    generated = models.DateTimeField(blank=True, null=True)
    submitted = models.DateTimeField(blank=True, null=True)
    input_gen = models.TextField(blank=True)
    output_gen = models.TextField(blank=True)
    output_user = models.FileField('Completed output file', blank=True, null=True, upload_to=get_fn_output)
    source = models.FileField('Source code', blank=True, null=True, upload_to=get_fn_source)
    language = models.ForeignKey('Language', blank=True, null=True)
    bonuses = models.ManyToManyField('Bonus', blank=True)

    class Meta:
        unique_together = ['challenge', 'author', 'set']

    def generate(self):
        # generate input/output on creation
        self.attempt += 1
        self.generated = datetime.now()

        # run generator script
        output = check_output(['python', self.challenge.generator.path, '%d' % self.set.id])
        if self.challenge.use_input_validation:
            self.input_gen = output
        else:
            self.input_gen = str(self.set.id)

        # run validator script
        p = Popen(['python', self.challenge.validator.path], stdin=PIPE, stdout=PIPE)
        self.output_gen = p.communicate(self.input_gen)[0]
        return output

    def is_expired(self):
        if self.set.time_limit <= 0:
            return False
        if not self.generated:
            return False
        else:
            return timezone.now() > self.generated + timedelta(seconds=self.set.time_limit+GRACE_PERIOD)

    def get_time_left(self):
        s = self.set.time_limit + GRACE_PERIOD - (timezone.now() - self.generated).total_seconds()
        minute = int(s / 60)
        second = int(s % 60)
        return '%d:%02d' % (minute, second)

    def apply_bonuses(self):
        bonuses = self.challenge.bonuses.all()
        b_ids = [b.id for b in bonuses]
        if 1 in b_ids and self.has_runtime_bonus():
            self.bonuses.add(Bonus.objects.get(id=1))
        if 2 in b_ids and self.has_earlybird_bonus():
            self.bonuses.add(Bonus.objects.get(id=2))
        if 3 in b_ids and self.has_first_post_bonus():
            self.bonuses.add(Bonus.objects.get(id=3))

    def has_earlybird_bonus(self):        
        return self.set.id == 2 and self.submitted and self.submitted < self.challenge.started + timedelta(hours=24)

    def has_runtime_bonus(self):
        return self.set.id == 2 and self.submitted and self.submitted < self.generated + timedelta(seconds=65)

    def has_first_post_bonus(self):
        n_solutions = self.challenge.solution_set.filter(set_id=5).count()
        return self.set.id == 5 and n_solutions == 1
        
class Bonus(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100)
    points = models.IntegerField(default=0)
    def __unicode__(self):
        return self.title
    class Meta:
        verbose_name_plural = 'bonuses'

class Language(models.Model):
    name = models.CharField(max_length=100)
    extension = models.CharField(max_length=5)
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']        