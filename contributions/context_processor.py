# local Django
from contributions.models import Developer, Project, Tag


def tags_processor(request):
    # project = Project.objects.get(project_name="Apache Ant")
    project_id = request.session['project']
    if project_id is not None:
        project = Project.objects.get(id=project_id)
    else:
        project = Project.objects.all().first()

    tags = Tag.objects.filter(project=project, major=True).order_by("pk")
    developers = Developer.objects.all().order_by("name")
    projects = Project.objects.all()

    return {'tags': tags, 'project': project, 'projects': projects, 'developers': developers}
