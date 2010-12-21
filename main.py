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
        # Get the Spiel Des Jahres award winners.
        query = [{
          "type": "/games/game",
          "id":   None,
          "name": None,
          "guid": None,
          "!/award/award_honor/honored_for": {
            "award": {
              "id": "/en/spiel_des_jahres"
            },
            "year": {
              "value": None,
              "limit": 1
            },
            "limit": 1
          },
          "sort": "-!/award/award_honor/honored_for.year.value"
        }]
        result = freebase.sandbox.mqlread(query)
        logging.info(result)

        # Keys with special characters, like "!/award/award_honor/honored_for"
        # cannot be accessed from a Django template, so rebuild the result
        # into a array of key-value pair dictionaries.
        games = []
        count = 0
        for r in result:
            name = r.name
            guid = r.guid
            year = r["!/award/award_honor/honored_for"].year.value
            game = {}
            game["name"] = name
            game["guid"] = guid
            game["year"] = year
            games.append(game)
            
        template_values = {
            'games': games
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

        # Get Game data
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
