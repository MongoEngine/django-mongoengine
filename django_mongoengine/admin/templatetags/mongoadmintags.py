from django import template
from django.conf import settings

register = template.Library()

class CheckGrappelli(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name
    def render(self, context):
        context[self.var_name] = 'grappelli' in settings.INSTALLED_APPS
        return ''

def check_grappelli(parser, token):
    """
    Checks weather grappelli is in installed apps and sets a variable in the context.
    Unfortunately there is no other way to find out if grappelli is used or not. 
    See: https://github.com/sehmaschine/django-grappelli/issues/32
    
    Usage: {% check_grappelli as <varname> %}
    """
    
    bits = token.contents.split()
    
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "'check_grappelli' tag takes exactly two arguments."
    
    if bits[1] != 'as':
        raise template.TemplateSyntaxError, "The second argument to 'check_grappelli' must be 'as'"
    varname = bits[2]
    
    return CheckGrappelli(varname)

register.tag(check_grappelli)
