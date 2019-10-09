from contributions.models import Tag


def tags_processor(request):
 tags = Tag.objects.all().order_by("description")
 return {'tags': tags}