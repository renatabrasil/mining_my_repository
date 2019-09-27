from django import template

register = template.Library()

# returns a value of a given array
@register.filter()
def get(value, arg):
    return value[arg]

@register.filter()
def get_field(value, args):
    if args is None:
        return False
    arg_list = [arg.strip() for arg in args.split(',')]
    index = int(arg_list[0])
    object = value[int(arg_list[0])]
    return getattr(object[index],arg_list[1])