# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
import main
import models
import gamebase
import time

from settings import *

import freebase
import logging

from google.appengine.api import taskqueue
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
 