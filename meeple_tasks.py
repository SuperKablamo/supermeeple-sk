# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
from __future__ import with_statement

import main
import freebase
import gamebase

from settings import *

import logging
import models
import time
import urllib2

from google.appengine.api import files
from google.appengine.api import images
from google.appengine.api import taskqueue
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

############################# METHODS ########################################
##############################################################################
def flushSeedGames():
    q = models.GameSeed.all()
    results = q.fetch(5000)
    for r in results:
        r.delete()

def seedGames():   
    '''Queries Freebase for all games.  Stores IDs in models.GameSeed.
    ''' 
    logging.info("################## main.py:: seedGames() ################")   
    query = {
        "type":   "/games/game",
        "mid":    None,
        "name":   None,
        "key": {
            "namespace":BGG_NAMESPACE,
            "value":     None,
            "optional":  True
            }
        }
    results = freebase.mqlreaditer(query, extended=True)
    count = 0
    for r in results:
        logging.info("################ result:: "+str(r)+" #################")    
        mid = r.mid
        if r.key is None: bgg_id = None
        else: bgg_id = r.key.value     
        name = r.name
        game_seed = models.GameSeed.get_by_key_name(mid)
        if game_seed is None:
            game_seed = models.GameSeed(key_name=mid, 
                                        mid=mid, 
                                        bgg_id=bgg_id,
                                        name=name)
                                        
            logging.info("############# game_seed.put() ####################")
            game_seed.put()
        count += 1     
        logging.info("############### Count:: "+str(count)+" ###############")    
    logging.info("################ Total count:: "+str(count)+" ############")            
    return True  

def processGameSeeds(keys, task_number):
    '''Iterates through GameSeed keys and builds a Game entity for each one
    using BGG data if available.
    '''
    _trace = TRACE+'processGameSeeds():: '
    logging.info(_trace)    
    game_seeds = models.GameSeed.get(keys)
    for gs in game_seeds:
        logging.info(_trace+' Processing game '+gs.name)
        logging.info(_trace+' Task number '+str(task_number))
        # First, try to match any games that are missing a bgg_id
        bgg_id = gs.bgg_id
        mid = gs.mid
        if bgg_id is not None: # Valid bgg_id, so build a game
            logging.info(_trace+' bgg_id = '+str(bgg_id))            
            # Use BGG XML API to get Game data
            game_data = checkinbase.parseBGGXML(bgg_id)
            if game_data is None: 
                logging.info(_trace+' Unable to parse BGGXML!')
            else: 
                gamebase.buildGame(mid, bgg_id)
                gs.processed = True
                gs.put()        
    logging.info(_trace+' exiting ...')
    return True    

def createBadges():
    '''Creates Badges and loads necessary images to the Blobstore.
    '''
    _trace = TRACE+'createBadges():: '
    logging.info(_trace)    
    base_url = 'http://www.supermeeple.com/static/images/badges/'    
    mime_type = 'image/png'
    
    # Load Badges
    updated = []    
    for b in BADGES:
        badge = models.Badge.get_by_key_name(b['key'])
        if badge is None:
            logging.info(_trace+'creating Badge '+b['key'])
            
            # Get *image* file for this Badge
            image_name = b['key']+'.png'
            logging.info(_trace+'image_name = '+image_name)
            image_blob_key = updateBlobStore(base_url, 
                                             image_name, 
                                             mime_type)
            
            # Get *banner* file for this Badge
            banner_name = b['key']+'_BANNER.png'
            logging.info(_trace+'banner_name = '+banner_name)
            banner_blob_key = updateBlobStore(base_url, 
                                              banner_name, 
                                              mime_type)
                                                          
            image_url = images.get_serving_url(str(image_blob_key))
            banner_url = images.get_serving_url(str(banner_blob_key))
                        
            badge = models.Badge(key_name=b['key'], 
                                 name=b['name'], 
                                 description=b['name'],
                                 image=image_blob_key,
                                 image_url=image_url,
                                 banner=banner_blob_key,
                                 banner_url=banner_url)
            
            updated.append(badge)
   
    db.put(updated)
    return None


def updateBlobStore(url, file_name, mime_type):
    '''Uploads an image to the BlobStore.
    '''
    _trace = TRACE+'storeImage():: '
    logging.info(_trace)
    
    # Get image file for this Badge
    logging.info(_trace+'file_name = '+file_name)
    q = blobstore.BlobInfo.all()            
    q.filter('filename =', file_name)
    blob_file = q.get()
    
    if blob_file is None:
        url = url+file_name
        logging.info(_trace+'url = '+url)
        _file = urllib2.urlopen(url)
        file_name = files.blobstore.create(mime_type=mime_type, 
                                           _blobinfo_uploaded_filename=file_name)
                                           
        with files.open(file_name, 'a') as f:
            f.write(_file.read())
        files.finalize(file_name)   
        blob_key = files.blobstore.get_blob_key(file_name) 
    else:    
        blob_key = blob_file.key()
    
    return blob_key

    
 