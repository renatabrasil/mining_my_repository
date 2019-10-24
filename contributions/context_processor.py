from contributions.models import Tag, Project


def tags_processor(request):
 project = Project.objects.get(project_name="Apache Ant")
 tags = Tag.objects.all().order_by("pk")

 return {'tags': tags, 'project': project}