#
# Copyright 2010 SuperKablamo, LLC
#

FACEBOOK_APP_ID = "149881721731503"
FACEBOOK_APP_SECRET = "8e79a7b1a2a58bc4824312094092c03e"

import os
import cgi
import freebase
import logging
import facebook
import models

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from urlparse import urlparse


class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    @property
    def current_user(self):
        logging.info('########### BaseHandler:: current_user ###########')
        logging.info('########### ' +FACEBOOK_APP_ID+'###########')
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = models.User.get_by_key_name(cookie["uid"])
                if not user:
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = models.User(key_name=str(profile["id"]),
                                       id=str(profile["id"]),
                                       name=profile["name"],
                                       profile_url=profile["link"],
                                       access_token=cookie["access_token"])
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()
                self._current_user = user
        return self._current_user



class MainHandler(BaseHandler):
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
        result = freebase.mqlread(query)
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
            'games': games,
            'current_user': self.current_user,
            'facebook_app_id': FACEBOOK_APP_ID
        }        
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'base_index.html'))
        self.response.out.write(template.render(path, template_values, debug=True))
 
class GameProfile(BaseHandler):
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
            'weblink': weblink,
            'current_user': self.current_user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'base_game.html'))
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
            "mid":           None,
            "type":          "/games/game",
            "name":          None,
            "creator":       [],
            "expansions":    [],
            "introduced":    None,
            "genre":         [],
            "designer":      [],
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

        result = freebase.mqlread(query, extended=True)
        
        # Can't access properties with special charactes in Django, so create
        # a dictionary.
        playerMinMax = result["/games/game/number_of_players"]
        weblink = result["/common/topic/weblink"]

        # create/update Game data
        entity = models.Game.get_by_key_name(result.mid)
        if not entity:
            entity = models.Game(key_name=result.mid, name=result.name)
            logging.info('## CREATING NEW ENTITY: KEY: ' + str(entity.key()) + 
                         ' | NAME: ' + entity.name)
                              
        else:
            entity.name = result.name            
            logging.info('## UPDATING ENTITY: KEY: ' + str(entity.key()) + 
                         ' | NAME: ' + entity.name)
        
        entity.put()
                              
        template_values = {
            'game': entity,
            'result': result,
            'playerMinMax': playerMinMax,
            'weblink': weblink, 
            'current_user': self.current_user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'base_game.html'))
        self.response.out.write(template.render(path, template_values, debug=True))

class GameCheckin(BaseHandler):
    
    # Checkin to Game
    def post(self):
        logging.info('########### GameCheckin::post ###########')
        data = getGame(self.request.get('mid'))
        
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
            'weblink': weblink, 
            'current_user': self.current_user,
            'facebook_app_id': FACEBOOK_APP_ID
        }
        
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'base_game.html'))
        self.response.out.write(template.render(path, template_values, debug=True))

######################## METHODS #############################################

def getGame(mid):
    """Returns a Freebase emql result for Game data.    
    """
    query = {
      "mid":           mid,
      "type":          "/games/game",
      "name":          None,
      "creator":       None,
      "expansions":    [],
      "introduced":    None,
      "genre":         [],
      "designer":      [],
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
    result = freebase.mqlread(query, extended=True)   
    return result
    
##############################################################################
application = webapp.WSGIApplication(
                                     [('/', MainHandler),
                                     ('/game-profile', GameProfile),
                                     (r'/game-profile(/m/.*)', GameProfile),
                                     ('/game-checkin', GameCheckin)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
