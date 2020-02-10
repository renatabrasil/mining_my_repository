# Django
from django.contrib import admin

# local Django
from .models import Developer, Directory, Project, Tag

# Register your models here.

admin.site.register(Developer)
admin.site.register(Project)
admin.site.register(Tag)
admin.site.register(Directory)
