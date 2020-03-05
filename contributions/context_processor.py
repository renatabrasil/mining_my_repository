# local Django
from contributions.models import Developer, Project, Tag


def tags_processor(request):
 project = Project.objects.get(project_name="Apache Ant")
 tags = Tag.objects.filter(project=project).order_by("pk")
 developers = Developer.objects.all().order_by("name")

 return {'tags': tags, 'project': project, 'developers': developers}
