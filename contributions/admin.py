from django.contrib import admin
from .models import Developer, Project, Tag

# Register your models here.

admin.site.register(Developer)
admin.site.register(Project)
admin.site.register(Tag)