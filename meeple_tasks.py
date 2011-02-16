#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

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
    logging.info('##########################################################')
    logging.info('#################### processGameSeeds(keys, task_number) #')
    logging.info('##########################################################')    
    game_seeds = models.GameSeed.get(keys)
    for gs in game_seeds:
        logging.info('################ Processing game '+gs.name+' #########')
        logging.info('################ Task number '+str(task_number)+' ####')
        # First, try to match any games that are missing a bgg_id
        bgg_id = gs.bgg_id
        mid = gs.mid
        if bgg_id is None:
            logging.info('################# bgg_id = None, find a match ####')
            name = gs.name
            bgg_id = gamebase.getBGGIDFromBGG(name)
        if bgg_id is not None: # Valid bgg_id, so build a game
            logging.info('################# bgg_id = '+str(bgg_id)+' #######')            
            gamebase.buildGame(mid, bgg_id)
            gamebase.storeBGGIDtoFreebase(mid, bgg_id)  
            time.sleep(10) 
        else: # No bgg_id found, make a note
            logging.info('################# bgg_id = None, make a note #####')  
            gs.bgg_id = None        
        gs.processed = True
        gs.put()        
    logging.info('######### exiting processGameSeeds(keys, task_number) ####')
    return True     
 