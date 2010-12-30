#
# Copyright 2010 SuperKablamo, LLC
#

FACEBOOK_APP_ID = "149881721731503"
FACEBOOK_APP_SECRET = "8e79a7b1a2a58bc4824312094092c03e"
DEBUG = True
CHECKIN_FREQUENCY = 600 # Checkin frequency in seconds
UPDATE_FREQUENCY = 604800 # Game data update frequency in seconds
BGG_XML_URI = "http://www.boardgamegeek.com/xmlapi/boardgame/"

import os
import cgi
import freebase
import logging
import facebook
import models
import datetime
import urllib2

from urlparse import urlparse
from xml.etree import ElementTree 
from django.utils import simplejson
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

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

    def generate(self, template_name, template_values):
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', template_name))
        self.response.out.write(template.render(path, template_values, debug=DEBUG))

class MainHandler(BaseHandler):
    """Return content for index.html.    
    """
    def get(self):
        logging.info('########### MainHandler:: get() ###########')
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
          "key" : {
            "namespace" : "/user/pak21/boardgamegeek/boardgame",
            "value" : None
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
            bgg_id = r.key.value
            game = {}
            game["name"] = name
            game["year"] = year
            game["mid"] = mid
            game["bgg_id"] = bgg_id
            games.append(game)
            
        template_values = {
            'games': games,
            'current_user': self.current_user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_index.html', template_values) 
 
class GameProfile(BaseHandler):
    """Returns a Game data
    
    GET - uses an mid to look up a Game on Freebase.  The datastore is 
    updated with Game data and the data is passed to a template.
    
    POST - uses gameID and gameName to look up a Game on Freebase.  The
    datastore is updated with Game data and the data is passed to a template.
    """
    # Direct linking to Game Profile
    def get(self, mid=None, bgg_id=None):
        logging.info('########### GameProfile::get ###########')
        logging.info('########### uri = ' + self.request.url + ' ###########')
        logging.info('########### mid = ' + mid + ' ###########')

        fb_game = getFBGame(mid)
        bgg_game = getBGGGame(mid=mid, bgg_id=bgg_id)
        user = self.current_user
        # Can't access properties with special charactes in Django, so create
        # a dictionary.
        playerMinMax = fb_game["/games/game/number_of_players"]
        weblink = fb_game["/common/topic/weblink"]

        # Create/Update Game data
        game = models.Game.get_by_key_name(fb_game.mid)
        if not game:
            game = models.Game(key_name=fb_game.mid, name=fb_game.name)
            logging.info('## CREATING NEW ENTITY: KEY: ' + str(game.key()) + 
                         ' | NAME: ' + game.name)
                              
        else:
            game.name = fb_game.name            
            logging.info('## UPDATING ENTITY: KEY: ' + str(game.key()) + 
                         ' | NAME: ' + game.name)
        
        game.put()
        checkin = getCheckin(game, user) 
                                                  
        template_values = {
            'bgg_game': bgg_game,
            'fb_game': fb_game,
            'playerMinMax': playerMinMax,
            'weblink': weblink,
            'checkin': checkin,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_game.html', template_values) 
          
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
                },
            "key" : {
              "namespace" : "/user/pak21/boardgamegeek/boardgame",
              "value" : None
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
            entity = models.Game(key_name=result.mid, name=result.name, bggID=result.key.value)
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
        self.generate('base_game.html', template_values) 

class GameCheckin(BaseHandler):
    
    # Checkin to Game
    def post(self):
        logging.info('########### GameCheckin::post ###########')
        user = self.current_user
        mid = self.request.get('mid')
        game = models.Game.get_by_key_name(mid)
        logging.info('########### GameCheckin:: game: ' + game.name +  '###########')

        gameCheckin = models.GameCheckin(user=user, game=game)
                                         
        gameCheckin.put()   
        q = models.GameCheckin.all()
        q = q.filter("game", game)
        checkin = q.fetch(1)    
        logging.info('########### GameCheckin:: checkin: ' + str(checkin) +  '###########')
                                              
                              
        template_values = {
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }
        self.generate('base_game.html', template_values) 

class GameCheckinTest(BaseHandler):
    # Checkin to Game
    def post(self):
        logging.info('########### GameCheckin::post ###########')
        user = self.current_user
        mid = self.request.get('mid')
        game = models.Game.get_by_key_name(mid)
        logging.info('########### GameCheckin:: game: ' + game.name +  '###########')

        # Check user into game
        gameCheckin = models.GameCheckin(user=user, game=game)
        gameCheckin.put()   
        q = models.GameCheckin.all()
        q = q.filter("game", game)
        checkin = q.fetch(1)    
        logging.info('########### GameCheckin:: checkin: ' + str(checkin) +  '###########')

        # Announce checkin on Facebook Wall
        logging.info('########### user.access_token = ' + user.access_token  + ' ###########')
        message = "I'm playing " + game.name
        results = facebook.GraphAPI(user.access_token).put_wall_post(message)
        
        template_values = {
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  

######################## METHODS #############################################

def getBGGGame(bgg_id, mid):
    logging.info('########### getBGGGame:: BUILDING BGGGAME ###########')
    # Use BGG XML API to get Game data
    game_url = BGG_XML_URI + bgg_id
    result = urllib2.urlopen(game_url).read()
    xml = ElementTree.fromstring(result)
    # Parse data
    name = xml.findtext(".//name")
    description = xml.findtext(".//description")
    year_published = strToInt(xml.findtext(".//yearpublished"))
    min_players = strToInt(xml.findtext(".//minplayers"))
    max_players = strToInt(xml.findtext(".//maxplayers"))
    playing_time = strToInt(xml.findtext(".//playingtime"))
    age = strToInt(xml.findtext(".//age"))
    publishers = buildDataList(xml.findall(".//boardgamepublisher"))
    artists = buildDataList(xml.findall(".//boardgameartist"))
    designers = buildDataList(xml.findall(".//boardgamedesigner"))    
    expansions = buildDataList(xml.findall(".//boardgameexpansion"))
    categories = buildDataList(xml.findall(".//boardgamecategory"))
    mechanics = buildDataList(xml.findall(".//boardgamemechanic"))

    
    # Create/Update Game
    game = models.Game.get_by_key_name(mid)
    game_xml = models.GameXML.get_by_key_name(bgg_id)
    if game: # Update Game
        time = datetime.datetime.now() - datetime.timedelta(0, UPDATE_FREQUENCY)
        # Only update if the last update is older than the allowed time
        if game.updated < time:
            game.name = name
            game.description = description
            game.year_published = year_published
            game.min_players = min_players
            game.playing_time = playing_time
            game.age = age
            game.publishers = publishers
            game.artists = artists
            game.designers = designers  
            game.expansions = expansions
            game.categories = categories
            game.mechanics = mechanics
            
            game_xml.xml = str(xml)
        
    else: # Create new Game
        game = models.Game(key_name=mid,
                           name=name,
                           description=description,
                           year_published = year_published,
                           min_players = min_players,
                           playing_time = playing_time,
                           age = age,
                           publishers = publishers,
                           artists = artists,
                           designers = designers,
                           expansions = expansions,
                           categories = categories,
                           mechanics = mechanics)
        
        game_xml = models.GameXML(key_name=bgg_id, xml=str(xml))                   
    
    game.put() # Save Game
    game_xml.put() # Save GameXML
    return game

def buildDataList(list):
    data_list = []
    for d in data_list:
        data_list.append(d.text)
    
    return data_list

def strToInt(s):
    """ Returns an integer formatted from a string.  Or 0, if string cannot be
    formatted.
    """
    try:
        i = int(s)
    except ValueError:
        i = 0    
    return i    

def getFBGame(mid):
    """Returns a JSON result for Freebase Game data.    
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
      },
      "key" : {
        "namespace" : "/user/pak21/boardgamegeek/boardgame",
        "value" : None
      }
    }       
    return freebase.mqlread(query, extended=True)   

def getCheckin(game, user):
    """Returns a checkin for the user and game.  Checkins that are not older
    than the CHECKIN_FREQUENCY are not returned, indicating that the user
    cannot checkin again.    
    """
    time = datetime.datetime.now() - datetime.timedelta(0, CHECKIN_FREQUENCY)
    q = models.GameCheckin.all()
    q.filter("game", game)
    q.filter("user", user)
    q.filter("created >", time)
    q.order("-created")
    checkin = q.get()
    return checkin
    
##############################################################################
application = webapp.WSGIApplication(
                                     [('/', MainHandler),
                                     ('/game-profile', GameProfile),
                                     (r'/game-profile(/m/.*)(/.*)', GameProfile),
                                     ('/game-checkin', GameCheckin),
                                     ('/game-checkin-test', GameCheckinTest)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
