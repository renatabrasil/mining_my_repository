from contributions.models import Tag


def line_base():
    line1_9_x = Tag.objects.get(description='rel/1.9.x').pk
    line1_10_0 = Tag.objects.get(description='rel/1.10.0').pk
    return [i for i in Tag.line_major_versions() if i != line1_9_x and i != line1_10_0]


def line_1_10_x():
    return Tag.line_base().append(Tag.objects.get(description='rel/1.10.0').pk)


def line_1_9_x():
    return Tag.line_base().append(Tag.objects.get(description='rel/1.9.x').pk)
