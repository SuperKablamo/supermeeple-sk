#
# Copyright 2010 SuperKablamo, LLC
#
import logging

from xml.etree import ElementTree 

def findPrimaryName(element_tree):
    """Returns the name of a BGG game where primary = true.
    """
    #logging.info('########### findPrimaryName::  ###########')    
    names = element_tree.findall(".//name")
    for n in names:
        #logging.info('########### n = ' + n.text + ' ###########')
        value = n.get("primary")
        if value == "true":
            name = n.text
            #logging.info('########### Found primary! name = ' + name + ' ###########')       
            return name
    
    name = xml.findtext(".//name")
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
    return i
    
    