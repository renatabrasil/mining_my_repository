from django import template

register = template.Library()

class SetVarNode(template.Node):

    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] = value

        return u""

# returns a value of a given array
@register.filter()
def get(value, arg):
    if arg in value:
        return value[arg]
    return None

@register.filter(name="get_list")
def get_list(value, arg):
    if value:
        return value[arg]
    return None

@register.filter()
def div(value, arg):
    if arg == 0:
        return 0
    return value/arg

@register.filter
def percentage(value):
    return format(value, ".2%")

@register.filter()
def get_field(value, args):
    if args is None:
        return False
    arg_list = [arg.strip() for arg in args.split(',')]
    index = int(arg_list[0])
    object = value[int(arg_list[0])]
    return getattr(object[index],arg_list[1])

@register.tag(name='set')
def set_var(parser, token):
    """
    {% set some_var = '123' %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form: {% set <var_name> = <var_value> %}")

    return SetVarNode(parts[1], parts[3])