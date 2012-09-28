from django.contrib import admin
from models import *

class ProblemAdmin(admin.ModelAdmin):
    list_display = ['title','author','status','created','started','completed']
    filter_horizontal = ['sets', 'bonuses']
    
class SolutionAdmin(admin.ModelAdmin):
    list_display = ['problem','author','set','attempt','status','generated']

class SetAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'points', 'time_limit']
    list_editable = ['title', 'points', 'time_limit']

class BonusAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'description', 'icon', 'points']

admin.site.register(Language)    
admin.site.register(Bonus, BonusAdmin)
admin.site.register(Set, SetAdmin)
admin.site.register(Problem, ProblemAdmin)
admin.site.register(Solution, SolutionAdmin)