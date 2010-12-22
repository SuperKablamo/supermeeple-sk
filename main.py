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
from urlparse import urlparse

import models

class MainHandler(webapp.RequestHandler):
    """Return content for index.html.    
    """
    def get(self):
        # Get the Spiel Des Jahres award winners.
        query = [{
          "type": "/games/game",
          "mid": None,
          "name": None,
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

        # Properties with special characters, like 
        # "!/award/award_honor/honored_for" cannot be accessed from a Django
        # template, so rebuild the result into a array of key-value pair 
        # dictionaries.
        games = []
        count = 0
        for r in result:
            name = r.name
            year = r["!/award/award_honor/honored_for"].year.value
            mid = r.mid
            game = {}
            game["name"] = name
            game["year"] = year
            game["mid"] = mid
            games.append(game)
            
        template_values = {
            'games': games
        }        
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'index.html'))
        self.response.out.write(template.render(path, template_values, debug=True))
 
class GameProfile(webapp.RequestHandler):
    """Returns a Game data
    
    GET - uses a guid to look up a Game on Freebase.  The datastore is 
    updated with Game data and the data is passed to a template.
    
    POST - uses gameID and gameName to look up a Game on Freebase.  The
    datastore is updated with Game data and the data is passed to a template.
    """
    # Direct linking to Game Profile
    def get(self, mid=None):
        logging.info('########### GameProfile::get ###########')
        logging.info('########### uri = ' + self.request.url + ' ###########')
        logging.info('########### mid = ' + mid + ' ###########')

        data = getGame(mid)
        
        # Can't access properties with special charactes in Django, so create
        # a dictionary.
        playerMinMax = data["/games/game/number_of_players"]
        weblink = data["/common/topic/weblink"]

        # create/update Game data
        entity = models.Game.get_by_key_name(data.mid)
        if not entity:
            entity = models.Game(key_name=data.mid, name=data.name)
            logging.info('## CREATING NEW ENTITY: KEY: ' + str(entity.key()) + 
                         ' | NAME: ' + entity.name)
                              
        else:
            entity.name = data.name            
            logging.info('## UPDATING ENTITY: KEY: ' + str(entity.key()) + 
                         ' | NAME: ' + entity.name)
        
        entity.put()
                              
        template_values = {
            'game': data,
            'playerMinMax': playerMinMax,
            'weblink': weblink
        }  

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'game.html'))
        self.response.out.write(template.render(path, template_values, debug=True))    
    # Game search POST
    def post(self):
        logging.info('########### GameProfile::post ###########')
        
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
            "minimum_age_years": None,
            "origin":        None,
            "publisher":     [],
            "derivative_games": [],
            "maximum_playing_time_minutes": None,
            "playing_time_minutes": None,
            "/games/game/number_of_players": {
                "high_value": None,
                "low_value":  None,
                "optional": True
                },  
            "/common/topic/weblink": {
                "description": "BoardGameGeek",
                "url":        None,
                "optional": True
                }
            }         

        result = freebase.sandbox.mqlread(query, extended=True)
        
        # Can't access properties with special charactes in Django, so create
        # a dictionary.
        playerMinMax = result["/games/game/number_of_players"]
        weblink = result["/common/topic/weblink"]

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
            'result': result,
            'playerMinMax': playerMinMax,
            'weblink': weblink
        }  

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'game.html'))
        self.response.out.write(template.render(path, template_values, debug=True))

application = webapp.WSGIApplication(
                                     [('/', MainHandler),
                                     ('/game-profile', GameProfile),
                                     (r'/game-profile(/m/.*)', GameProfile)],
                                     debug=True)

def getGame(mid):
    """Returns a Freebase emql result for Game data.    
    """
    query = {
      "mid":           mid,
      "id":            None,
      "type":          "/games/game",
      "name":          None,
      "creator":       None,
      "expansions":    [],
      "introduced":    None,
      "genre":         [],
      "designer":      None,
      "minimum_age_years": None,
      "origin":        None,
      "publisher":     [],
      "derivative_games": [],
      "maximum_playing_time_minutes": None,
      "playing_time_minutes": None,
      "/games/game/number_of_players": {
        "high_value": None,
        "low_value":  None,
        "optional": True
      },  
      "/common/topic/weblink": {
        "description": "BoardGameGeek",
        "url":        None,
        "optional": True
      }
    }        
    result = freebase.sandbox.mqlread(query, extended=True)   
    return result

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
