# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

from google.appengine.ext.webapp import template
from django import template as django_template

def in_list(value, arg):
  """
  Given an item and a list, check if the item is in the list.
  Usage:
  {% if item|in_list:list %} 
      in list 
  {% else %} 
      not in list
  {% endif %}
  """
  return value in arg

def checkedin(value, arg):
    time = datetime.datetime.now() - datetime.timedelta(0, CHECKIN_FREQUENCY)
    if value > time:
        return True
    else: return False
  
register = template.create_template_register()  
ifinlist = register.filter(in_list)
ifcheckedin = register.filter(checkedin)
