# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

import logging

from google.appengine.ext import db
from xml.etree import ElementTree 

def findPrimaryName(element_tree):
    """Returns the name of a BGG game where primary = true.
    """
    logging.info('########### findPrimaryName::  ###########')    
    names = element_tree.findall(".//name")
    for n in names:
        logging.info('########### n = ' + n.text + ' ###########')
        value = n.get("primary")
        if value == "true":
            name = n.text
            logging.info('########### Found primary! name = ' + name + ' ###########')       
            return name
    
    name = element_tree.findtext(".//name")
    #logging.info('########### No primary found :( name = ' + name + ' ###########')
    return name
    
def buildDataList(xml_element):
    """Returns a list of parsed xml subelements.
    """
    data = []
    for x in xml_element:
        data.append(x.text)
    return data

def strToInt(s):
    """ Returns an integer formatted from a string.  Or 0, if string cannot be
    formatted.
    """
    try:
        i = int(s)
    except ValueError:
        i = 0 
    except TypeError:
        i = 0       
    return i

def prefetch_refprops(entities, *props):
    """Dereference Reference Properties to reduce Gets.  See:
    http://blog.notdot.net/2010/01/ReferenceProperty-prefetching-in-App-Engine
    """
    fields = [(entity, prop) for entity in entities for prop in props]
    ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
    ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
    for (entity, prop), ref_key in zip(fields, ref_keys):
        prop.__set__(entity, ref_entities[ref_key])
    return entities  

def smart_truncate(content, length=100, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix 
