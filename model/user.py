# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
import os
import logging

from settings import *

############################# METHODS ########################################
##############################################################################

def createUser(graph, cookie):
    '''Returns a User model, built from the Facebook Graph API data.  
    '''
    # Build User from Facebook Graph API ...
    profile = graph.get_object("me")
    try: # If the user has no location set, make the default "Earth"
        loc_id = profile["location"]["id"]
        loc_name = profile["location"]["name"]
    except KeyError:
        loc_id = "000000000000001"
        loc_name = "Earth" 
    user = models.User(key_name=str(profile["id"]),
                       fb_id=str(profile["id"]),
                       name=profile["name"],
                       fb_profile_url=profile["link"],
                       fb_location_id=loc_id,
                       fb_location_name=loc_name,
                       access_token=cookie[TOKEN],
                       active = True)
    user.put() 
    return user
  
def updateUser(user, graph, cookie):
    '''Returns a User model, updated from the Facebook Graph API data.  
    '''
    _trace = TRACE+' updateUser() '
    logging.info(_trace)
    # Check for deauthorized users.
    #if user.active == False:
    #    return None
    access_token = cookie[TOKEN]
    logging.info(_trace+'access_token = '+access_token)    
    props = user.properties() # This is what's in the Datastore
    try:
        profile = graph.get_object("me") # This is what Facebook has
    except urllib2.HTTPError:
        logging.info(_trace+'HTTPError')
        return None
    new_profile_url = profile["link"]  
    try: # If the user has no location set, make the default "Earth"
        new_loc_id = profile["location"]["id"]
        new_loc_name = profile["location"]["name"]
    except KeyError:
        new_loc_id = "000000000000001"
        new_loc_name = "Earth"    
    update = False
    
    # Compare properties and only update if things have changed ...
    if user.active == False:
        user.active = True
        update = True
    if new_profile_url != props['fb_profile_url']:
        user.fb_profile_url = new_profile_url
        update = True
    if new_loc_id != props['fb_location_id']:
        user.fb_location_id = new_loc_id
        update = True
    if new_loc_name != props['fb_location_name']:
        user.fb_location_name = new_loc_name
        udpate = True
    if access_token != props[TOKEN]:    
        user.access_token = access_token
        update = True
    if update == True:
        user.put() 
    return user
    
def createLiteUser(name, fb_id):
    '''Returns a new User model, built using the minumum data requirements.
    '''
    logging.info(TRACE+' createLiteUser('+name+', '+fb_id+')')
    user = models.User(key_name=fb_id,
                       fb_id=fb_id,
                       name=name)    
    return user

def getFBUser(fb_id=None):
    '''Returns a User for the given fb_id.
    '''
    logging.info(TRACE+' getFBUser()')        
    user = models.User.get_by_key_name(fb_id)
    return user