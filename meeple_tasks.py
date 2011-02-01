#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import freebase
import logging
import main
import models

from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

############################# REQUEST HANDLERS ############################### 
##############################################################################   

class GameBuilder(webapp.RequestHandler):
    def get(self):
        logging.info('################# GameBuilder:: get ##################')

    def post(self):
        logging.info('################# GameBuilder:: post #################')
        bgg_id = self.request.get('bgg_id')
        mid = self.request.get('mid')
        game = main.getGame(bgg_id=bgg_id, mid=mid)  

class GameSeeder(webapp.RequestHandler):
    def get(self):
        logging.info('################# GameSeeder:: get ##################')

    def post(self):
        logging.info('################# GameSeeder:: post #################')
        seedGames()
  
############################# METHODS ########################################
##############################################################################
def seedGames():    
    logging.info("################## main.py:: seedGames() ################")   
    query = {
        "type":   "/games/game",
        "mid":    None,
        "key": {
            "namespace": "/user/pak21/boardgamegeek/boardgame",
            "value":     None,
            "optional":  False
            }
        }
    results = freebase.mqlreaditer(query, extended=True)
    for r in results:
        #logging.info("################ result:: "+str(r)+" #################")    
        mid = r.mid
        bgg_id = r.key.value
        game_seed = models.GameSeed.get_by_key_name(mid)
        if game_seed is None:
            game_seed = models.GameSeed(key_name=mid, mid=mid, bgg_id=bgg_id)
            game_seed.put()

    return True  
    
##############################################################################
##############################################################################
application = webapp.WSGIApplication([('/_ah/queue/build-games', GameBuilder),
                                      ('/_ah/queue/seed-games', GameSeeder)],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
