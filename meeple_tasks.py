#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import main
import models
import gamebase

from settings import *

import freebase
import logging

from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

############################# METHODS ########################################
##############################################################################

def seedGames():   
    '''Queries Freebase for all games.  Stores IDs in models.GameSeed.
    ''' 
    logging.info("################## main.py:: seedGames() ################")   
    query = {
        "type":   "/games/game",
        "mid":    None,
        "name":   None,
        "key": {
            "namespace": "/user/pak21/boardgamegeek/boardgame",
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

def buildGames():
    logging.info('#################### buildGames() ########################')
    q = models.GameSeed.all()
    config = models.Config.get_by_key_name(CONFIG_KEY_NAME)
    if config is None:
        config = models.Config(key_name=CONFIG_KEY_NAME,
                               cursor=None)

    cursor = config.game_seed_cursor        
    if cursor is not None: 
        logging.info('######### cursor = '+str(cursor)+ ' ##################')
        r = q.with_cursor(cursor)  
        game_seeds = r.fetch(10)        
    else: 
        game_seeds = q.fetch(10)
    config.game_seed_cursor = q.cursor()
    config.put()
    if game_seeds is None: return # No more results with this cursor
    for gs in game_seeds:
        logging.info('################# Building game '+gs.name+' ##########')
        # First, try to match any games that are missing a bgg_id
        bgg_id = gs.bgg_id
        mid = gs.mid
        if bgg_id is None:
            logging.info('################# bgg_id = None ##################')
            name = gs.name
            bgg_id = gamebase.getBGGIDFromBGG(name)
        # Valid bgg_id, so build a game.
        if bgg_id is not None:
            logging.info('################# bgg = '+str(bgg_id)+' ##########')            
            gamebase.buildGame(mid, bgg_id)
            gamebase.storeBGGIDtoFreebase(mid, bgg_id)   

    logging.info('################# exiting buildGames() ###################')
    freebase.logout()
    return      
 