# Request Handlers

import os
import cgi
import freebase
import logging

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import models

class MainHandler(webapp.RequestHandler):
    def get(self):
        logging.info('########### MainHandler::get ###########')
        #envelope = {"extended":True}
        #asof = None;
        query = {
            "id": "/en/settlers_of_catan",
            "/common/topic/weblink": [{
                "description": "BoardGameGeek",
                "url": None
            }]
        }
        result = freebase.sandbox.mqlread(query, extended=True)
        logging.info(result)
        
        foo = result["/common/topic/weblink"][0].url
        
        logging.info(foo) 
        
        template_values = {
            'result': result
        }
        
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'index.html'))
        self.response.out.write(template.render(path, template_values, debug=True))
 
class PostGame(webapp.RequestHandler):
    def post(self):
        logging.info('########### GetGame::post ###########')
        
        # store POST variables
        gameID = self.request.get('gameID')
        gameName = self.request.get('gameName')
        logging.info('gameID = ' + str(gameID) + 'gameName = ' + str(gameName))

        # query Freebase for Game data
        query = {
            "id":            str(gameID),
            "type":          "/games/game",
            "guid":          None,
            "name":          None,
            "creator":       None,
            "expansions":    [],
            "introduced":    None,
            "genre":         [],
            "designer":      None,
            "maximum_playing_time_minutes": None,
            "minimum_age_years": None,
            "number_of_players": None,
            "origin":        None,
            "playing_time_minutes": None,
            "publisher":     [],
            "derivative_games": [],
        }
        result = freebase.sandbox.mqlread(query)
        logging.info('gameID = ' + str(gameID) + 'gameName = ' + str(gameName))
        
        # create/update Game data
        entity = models.Game.get_by_key_name(result.guid)
        if not entity:
            entity = models.Game(key_name=result.guid,
                                 freebaseID=result.id,
                                 name=result.name)
                                 
            logging.info('## CREATING NEW ENTITY: KEY: ' + str(entity.key()) + 
                         ' | FREEBASEID: ' + entity.freebaseID +
                         ' | NAME: ' + entity.name)
                              
        else:
            entity.freebaseID = result.id  
            entity.name = result.name            

            logging.info('## UPDATING ENTITY: KEY: ' + str(entity.key()) + 
                         ' | FREEBASEID: ' + entity.freebaseID +
                         ' | NAME: ' + entity.name)
        
        entity.put()
                              
        template_values = {
            'game': entity,
            'result': result
        }  

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'game.html'))
        self.response.out.write(template.render(path, template_values, debug=True))

application = webapp.WSGIApplication(
                                     [('/', MainHandler),
                                     ('/game-profile', PostGame)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
