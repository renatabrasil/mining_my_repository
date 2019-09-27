from django import template

register = template.Library()

# returns a value of a given array
@register.filter()
def get(value, arg):
    return value[arg]