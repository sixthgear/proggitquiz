from django.contrib import admin
from models import *

class ProblemAdmin(admin.ModelAdmin):
    list_display = ['title','author','status','created','started','completed']
    
class SolutionAdmin(admin.ModelAdmin):
    list_display = ['problem','author','set','status','language','generated']

admin.site.register(Language)    
admin.site.register(Bonus)
admin.site.register(Set)
admin.site.register(Problem, ProblemAdmin)
admin.site.register(Solution, SolutionAdmin)