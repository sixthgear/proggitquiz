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

SOL_STATUS_CHOICES = (
    (0, 'Incomplete'),
    (1, 'Expired'),
    (2, 'Complete'),
)

def get_fn_generator(instance, filename):
    # slug = instance.title.lower().replace(' ','')
    slug = re.sub(r'[\W_]+', '', instance.title.lower())[:50]
    return 'generators/%s-gen.py' % slug

def get_fn_validator(instance, filename):
    slug = re.sub(r'[\W_]+', '', instance.title.lower())[:50]
    return 'validators/%s-val.py' % slug

def get_fn_output(instance, filename):
    fn, ext = os.path.splitext(filename)
    return 'output/p%03d-%d-%s.out' % (
        instance.problem.id, 
        instance.author.id, 
        instance.set.title.lower()[:3]
    )

def get_fn_source(instance, filename):
    fn, ext = os.path.splitext(filename)
    return 'source/p%03d-%s-%s%s' % (
        instance.problem.id, 
        instance.author.username, 
        instance.set.title.lower()[:3], 
        ext
    )

class Language(models.Model):
    name = models.CharField(max_length=100)
    extension = models.CharField(max_length=5)
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

class Set(models.Model):
    title = models.CharField(max_length=100)
    points = models.IntegerField()
    def __unicode__(self):
        return self.title

class Problem(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(User)
    status = models.IntegerField(choices=PRB_STATUS_CHOICES)
    created = models.DateField(auto_now_add=True)
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)
    preamble = models.TextField()
    body = models.TextField()
    generator = models.FileField(null=True, upload_to=get_fn_generator)
    validator = models.FileField(null=True, upload_to=get_fn_validator)
    # spoilers = models.BooleanField()
    def __unicode__(self):
        return self.title

class Solution(models.Model):
    problem = models.ForeignKey(Problem)
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
    language = models.ForeignKey(Language, blank=True, null=True)
    bonuses = models.ManyToManyField('Bonus', blank=True)

    class Meta:
        unique_together = ['problem', 'author', 'set']

    def generate(self):
        # generate input/output on creation
        self.attempt += 1
        self.generated = datetime.now()
        self.input_gen = check_output(['python', self.problem.generator.path, '%d' % self.set.id])
        p = Popen(['python', self.problem.validator.path], stdin=PIPE, stdout=PIPE)
        self.output_gen = p.communicate(self.input_gen)[0]

    def is_expired(self):
        if not self.generated:
            return False
        else:
            return timezone.now() > self.generated + timedelta(seconds=305)

    def get_time_left(self):
        s = 305 - (timezone.now() - self.generated).total_seconds()
        minute = int(s / 60)
        second = int(s % 60)
        return "%d:%02d" % (minute, second)

    def apply_bonuses(self):
        
        if self.has_runtime_bonus():
            self.bonuses.add(Bonus.objects.get(id=1))

        if self.has_earlybird_bonus():        
            self.bonuses.add(Bonus.objects.get(id=2))

    def has_earlybird_bonus(self):        
        return self.set.id == 2 and self.submitted and self.submitted < self.problem.started + timedelta(hours=12)

    def has_runtime_bonus(self):
        return self.set.id == 2 and self.submitted and self.submitted < self.generated + timedelta(seconds=65)

        
class Bonus(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100)
    points = models.IntegerField(default=0)
    def __unicode__(self):
        return self.title