#
# Copyright 2010 SuperKablamo, LLC
#
    
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
    
    