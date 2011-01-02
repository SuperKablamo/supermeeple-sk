#
# Copyright 2010 SuperKablamo, LLC
#

FACEBOOK_APP_ID = "149881721731503"
FACEBOOK_APP_SECRET = "8e79a7b1a2a58bc4824312094092c03e"
DEBUG = False
CHECKIN_FREQUENCY = 600 # Checkin frequency in seconds
UPDATE_FREQUENCY = 604800 # Game data update frequency in seconds
BGG_XML_URI = "http://www.boardgamegeek.com/xmlapi/boardgame/"
BGG_XML_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?exact=1&search="

import os
import cgi
import freebase
import logging
import facebook
import models
import datetime
import urllib2
from utils import strToInt
from utils import buildDataList
from utils import findPrimaryName

from urlparse import urlparse
from xml.etree import ElementTree 
from django.utils import simplejson
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
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
        query_spiel = [{
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
        query_meeple = [{
          "type": "/games/game",
          "mid": None,
          "name": None,
          "!/award/award_honor/honored_for": {
            "award": {
              "id": "/en/meeples_choice_award"
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
          "sort": "-!/award/award_honor/honored_for.year.value",
          "limit": 20
        }]        
        result_spiels = freebase.mqlread(query_spiel)
        result_meeples = freebase.mqlread(query_meeple)

        # Properties with special characters, like 
        # "!/award/award_honor/honored_for" cannot be accessed from a Django
        # template, so rebuild the result into a array of key-value pair 
        # dictionaries.
        spiel_games = []
        spiel_count = 0
        for r in result_spiels:
            name = r.name
            year = r["!/award/award_honor/honored_for"].year.value
            mid = r.mid
            bgg_id = r.key.value
            game = {}
            game["name"] = name
            game["year"] = year
            game["mid"] = mid
            game["bgg_id"] = bgg_id
            spiel_games.append(game)
            
        meeple_games = []
        meeple_count = 0
        for r in result_meeples:
            name = r.name
            year = r["!/award/award_honor/honored_for"].year.value
            mid = r.mid
            bgg_id = r.key.value
            game = {}
            game["name"] = name
            game["year"] = year
            game["mid"] = mid
            game["bgg_id"] = bgg_id
            meeple_games.append(game)            
        
        template_values = {
            'spiels': spiel_games,
            'meeples': meeple_games,
            'current_user': self.current_user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_index.html', template_values) 
 
class GameProfile(BaseHandler):
    """Returns a Game data
    
    GET - uses FB and BGG ids to build Game data for display. FB and BGG are
    queried for data, persisted to the Datastore (if new or updated), and the
    data is passed to HTML for display.
    
    POST - uses gameID and gameName to look up a Game on Freebase.  The
    datastore is updated with Game data and the data is passed to a template.
    """
    # Direct linking to Game Profile
    def get(self, mid=None, bgg_id=None):
        logging.info('########### GameProfile::get ###########')
        logging.info('########### mid = ' + mid + ' ###########')
        logging.info('########### bgg_id = ' + bgg_id + ' ###########')
        user = self.current_user
        game = getBGGGame(mid=mid, bgg_id=bgg_id)
        checkin = getCheckin(game, user) 
        template_values = {
            'game': game,
            'checkin': checkin,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_game.html', template_values) 
          
    # Game search POST
    def post(self):
        logging.info('########### GameProfile::post ###########')
        user = self.current_user
        # Store POST variables
        game_id = self.request.get('game_id')

        logging.info('########### game_id = ' + game_id + ' ###########')
        # Get bgg_id and mid
        game_ids = getBGGIDFromFB(game_id)
        
        if game_ids["bgg_id"] is not None: 
            game = getBGGGame(mid=game_ids["mid"], bgg_id=game_ids["bgg_id"])
            checkin = getCheckin(game, user)                
            template_values = {
                'game': game,
                'checkin': checkin,
                'current_user': user,
                'facebook_app_id': FACEBOOK_APP_ID
            }  
            self.generate('base_game.html', template_values)            
        else:  # The FB data does not have a BGG id.  
            logging.info('########### NO BGG ID :( ###########')
            game_name = self.request.get('game_name')
            bgg_id = getBGGIDFromBGG(game_name)
            if bgg_id is not None:
                logging.info('########### bgg_id = ' + str(bgg_id) + ' ###########')
                game = getBGGGame(mid=game_ids["mid"], bgg_id=bgg_id)
                checkin = getCheckin(game, user)                
                template_values = {
                    'game': game,
                    'checkin': checkin,
                    'current_user': user,
                    'facebook_app_id': FACEBOOK_APP_ID
                }  
                self.generate('base_game.html', template_values)                
            else:  # Return an empty Game.          
                game = models.Game(key_name="0",
                                   bgg_id="0",
                                   bgg_img_url=image_url,
                                   name=game_name,
                                   description="Data for this game was not found on Board Game Geek.")
                checkin = getCheckin(game, user)                
                template_values = {
                    'game': game,
                    'checkin': None,
                    'current_user': user,
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
        # Check user into game
        gameCheckin = models.GameCheckin(user=user, game=game)
        gameCheckin.put()   
        q = models.GameCheckin.all()
        q = q.filter("game", game)
        checkin = q.fetch(1)    
        logging.info('########### GameCheckin:: checkin: ' + str(checkin) +  '###########')
        # Announce checkin on Facebook Wall
        #### logging.info('########### user.access_token = ' + user.access_token  + ' ###########')
        #### message = "I'm playing " + game.name
        #### results = facebook.GraphAPI(user.access_token).put_wall_post(message)
        template_values = {
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  

######################## METHODS #############################################
def getBGGGame(bgg_id, mid):
    """Returns a BGGGame model that has been either created or update to the
    datastore.
    """
    logging.info('########### getBGGGame:: BUILDING BGGGAME ###########')
    #logging.info('########### bgg_id = ' + bgg_id + ' ###########')
    #logging.info('########### mid = ' + mid + ' ###########')
    # Use BGG XML API to get Game data
    game_url = BGG_XML_URI + bgg_id
    result = urllib2.urlopen(game_url).read()
    xml = ElementTree.fromstring(result)
    # Parse data
    name = findPrimaryName(xml)
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
    subdomains = buildDataList(xml.findall(".//boardgamesubdomain"))
    image_url = xml.findtext(".//image")
    
    # Create/Update Game
    game = models.Game.get_by_key_name(mid)
    game_xml = models.GameXML.get_by_key_name(bgg_id)
    decoded_result = result.decode("utf-8")
    xml_text = db.Text(decoded_result)
    if game: # Update Game
        time = datetime.datetime.now() - datetime.timedelta(0, UPDATE_FREQUENCY)
        # Only update if the last update is older than the allowed time
        if game.updated < time:
            game.name = name
            game.bgg_id = bgg_id
            game.bgg_img_url = image_url
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
            game.subdomains = subdomains
            game_xml.xml = xml_text
    else: # Create new Game
        game = models.Game(key_name=mid,
                           bgg_id=bgg_id,
                           bgg_img_url=image_url,
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
                           mechanics = mechanics,
                           subdomains = subdomains)
        game_xml = models.GameXML(key_name=bgg_id, xml=xml_text)                   
    game.put() # Save Game
    game_xml.put() # Save GameXML
    return game

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

def getBGGIDFromFB(game_id):
    """Returns the Board Game Geek Game ID and Freebase MID from Freebase.    
    """
    # This query will return None if there is no BGG key/id.
    query = {
      "id":            str(game_id),
      "mid":           None,
      "key" : {
        "namespace" : "/user/pak21/boardgamegeek/boardgame",
        "value" : None,
        "optional": True
      }
    }  
    result = freebase.mqlread(query, extended=True)
    if result.key is not None: # The FB game entry has a BGG id
        game_ids = {"bgg_id":result.key.value, "mid":result.mid}    
        return game_ids
    else:
        game_ids = {"bgg_id":None, "mid":result.mid}
        return game_ids   
        
def getBGGIDFromBGG(game_name):
    """Returns the Board Game Geek Game ID from Board Game Geek.    
    """
    logging.info('########### getBGGIDFromBGG:: finding bgg_id ###########')
    logging.info('########### game_name = ' + game_name + ' ###########')   
    game_url = BGG_XML_SEARCH + urllib2.quote(game_name)
    logging.info('########### game_url = ' + game_url + ' ###########') 
    result = urllib2.urlopen(game_url).read()
    xml = ElementTree.fromstring(result)
    bgg_id = xml.find("./boardgame").attrib['objectid']
    return bgg_id
    
def getCheckin(bgg_game, user):
    """Returns a checkin for the user and game.  Checkins that are not older
    than the CHECKIN_FREQUENCY are not returned, indicating that the user
    cannot checkin again.    
    """
    time = datetime.datetime.now() - datetime.timedelta(0, CHECKIN_FREQUENCY)
    q = models.GameCheckin.all()
    q.filter("game", bgg_game)
    q.filter("user", user)
    q.filter("created >", time)
    q.order("-created")
    checkin = q.get()
    return checkin
    
##############################################################################
application = webapp.WSGIApplication(
                                     [('/', MainHandler),
                                     ('/game-profile', GameProfile),
                                     (r'/game-profile(/m/.*)/(.*)', GameProfile),
                                     ('/game-checkin', GameCheckin)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
