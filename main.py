#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ######################################## 
import os
import cgi
import freebase
import logging
import facebook
import models
import datetime
import urllib2
import utils
from utils import strToInt
from utils import buildDataList
from utils import findPrimaryName

from settings import *
from urlparse import urlparse
from xml.etree import ElementTree 
from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

############################# REQUEST HANDLERS ###############################    
class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    @property
    def current_user(self):
        logging.info('############# BaseHandler:: current_user #############')
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = models.User.get_by_key_name(cookie["uid"])
                if not user: # Build a User
                    user = getUser(
                            facebook.GraphAPI(cookie["access_token"]),
                            cookie)
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()
                self._current_user = user
        return self._current_user

    def generate(self, template_name, template_values):
        template.register_template_library('templatefilters')
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, 
                            os.path.join('templates', template_name))

        self.response.out.write(template.render(path, 
                                                template_values, 
                                                debug=DEBUG))
                                                
class Admin(BaseHandler):
    def get(self, pswd=None):
        if pswd == "backyardchicken":
            template_values = {
                'current_user': self.current_user,
                'facebook_app_id': FACEBOOK_APP_ID
            }  
            self.generate('base_admin.html', template_values)
        else: self.redirect(500)  

class MainHandler(BaseHandler):
    """Return content for index.html.     
    """
    def get(self):
        logging.info('################# MainHandler:: get() ################')
        spiel_id = "/en/spiel_des_jahres"
        meeples_id = "/en/meeples_choice_award"
        spiels_cache = memcache.get(spiel_id)
        meeples_cache = memcache.get(meeples_id)
        # Freebases queries for award winners only occurs once - the first
        # time index.html is requested. To updated the results in index.html,
        # delete the appropriate entries in models.FBMQL.  This will force 
        # the query to be run again and refresh the results.
        if spiels_cache is None:
            spiel_game_award = models.GameAward.get_by_key_name(spiel_id)
            if spiel_game_award is None:
                query_spiel = [{
                    "type":"/games/game",
                    "mid":None,
                    "name":None,
                    "!/award/award_honor/honored_for": {
                        "award": {
                            "id":spiel_id
                        },
                        "year": {
                            "value":None,
                            "limit":1
                        },
                        "limit":1
                        },
                        "key" : {
                            "namespace":"/user/pak21/boardgamegeek/boardgame",
                            "value": None
                        },
                        "sort":"-!/award/award_honor/honored_for.year.value",
                        "limit":20
                    }] 
                result = freebase.mqlread(query_spiel) 
                json_dump = simplejson.dumps(result)
                json_dump_text = db.Text(json_dump)
                spiel_game_award = models.GameAward(key_name=spiel_id, 
                                                    json_dump=json_dump_text)
                spiel_game_award.put()
                spiels = parseGameAwards(spiel_game_award) 
                success = memcache.set(key=spiel_id, 
                                       value=spiels, 
                                       time=2592000) # expiration 30 days
                spiels_cache = spiels
            else:    
                spiels = parseGameAwards(spiel_game_award) 
                success = memcache.set(key=spiel_id, 
                                       value=spiels, 
                                       time=2592000) # expiration 30 days
                spiels_cache = spiels
                
        if meeples_cache is None:
            meeples_game_award = models.GameAward.get_by_key_name(meeples_id)
            if meeples_game_award is None:
                query_meeples = [{
                    "type": "/games/game",
                    "mid": None,
                    "name": None,
                    "!/award/award_honor/honored_for": {
                        "award": {
                            "id": meeples_id
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
                result = freebase.mqlread(query_meeples) 
                json_dump = simplejson.dumps(result)
                json_dump_text = db.Text(json_dump)
                meeples_game_award = models.GameAward(key_name=meeples_id, 
                                                      json_dump=json_dump_text)
                meeples_game_award.put()
                meeples = parseGameAwards(meeples_game_award) 
                success = memcache.set(key=meeples_id, 
                                       value=meeples, 
                                       time=2592000) # expiration 30 days
                meeples_cache = meeples
            else:
                meeples = parseGameAwards(meeples_game_award) 
                success = memcache.set(key=meeples_id, 
                                       value=meeples, 
                                       time=2592000) # expiration 30 days
                meeples_cache = meeples                     
                                       
        checkins = getLatestCheckins()       
        template_values = {
            'checkins': checkins,
            'spiels': spiels_cache,
            'meeples': meeples_cache,
            'current_user': self.current_user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_index.html', template_values) 
 
class GameProfile(BaseHandler):
    """Returns a Game data.
    
    GET - uses FB and BGG ids to build Game data for display. FB and BGG are
    queried for data, persisted to the Datastore (if new or updated), and the
    data is passed to HTML for display.
    
    POST - uses gameID and gameName to look up a Game on Freebase.  Then
    redirects to GET in order to display Game Profile.  POSTs come in via
    Freebase Suggest, and therefore only contain the Freebase ID and Name.
    """
    # Direct linking to Game Profile
    def get(self, mid=None, bgg_id=None):
        logging.info('################# GameProfile::get ###################')
        user = self.current_user
        game = getGame(mid=mid, bgg_id=bgg_id)
        checkins = getGameCheckins(game)
        host = self.request.host # used for Facebook Like url 
        checked_in = isCheckedIn(user)     
        template_values = {
            'checked_in': checked_in,
            'host': host,
            'game': game,
            'checkins': checkins,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_game.html', template_values) 

    # Game search POST
    def post(self):
        logging.info('################### GameProfile::post ################')
        user = self.current_user
        game_ids = getBGGIDFromFB(self.request.get('game_id'))
        mid = game_ids["mid"]
        bgg_id = game_ids["bgg_id"]
        if mid:
            if bgg_id:
                self.redirect('/game'+mid+'/'+bgg_id)
            else:
                self.redirect('/game'+mid+'/0') # 0 indicates no BGG_ID found
        else:
            self.error(500)
             
class UserProfile(BaseHandler):
    """Returns content for User Profile pages.
    """
    def get(self, user_fb_id=None):
        logging.info('################# UserProfile::get ###################')
        user = self.current_user # this is the logged in User
        profile_user = getFBUser(user_fb_id)
        checkins = getUserCheckins(profile_user)
        template_values = {
            'checkins': checkins,
            'profile_user': profile_user,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_user.html', template_values)

class Checkin(BaseHandler):
    # Checkin to Game
    def post(self):
        logging.info('#################### Checkin::post ###################')
        user = self.current_user
        mid = self.request.get('mid')
        bgg_id = self.request.get('bgg_id')
        name = self.request.get('name')
        message = self.request.get('message')
        share = self.request.get('facebook')
        thumbnail = self.request.get('thumbnail')
        game_key = db.Key.from_path('Game', mid)
        # Check user into game
        badges = createCheckin(user, game_key, facebook)
        if share.upper() == 'TRUE':# Announce checkin on Facebook Wall
            logging.info('#### posting to Facebook '+user.access_token+'####')
            attachment = {}
            url = 'http://www.supermeeple.com' + mid + '/' + bgg_id
            attachment['caption'] = "supermeeple.com"
            attachment['link'] = url #url
            attachment['name'] = name
            attachment['picture'] = thumbnail
            results = facebook.GraphAPI(
               user.access_token).put_wall_post(message, attachment)
        self.response.headers.add_header("content-type", "application/json")       
        return self.response.out.write(simplejson.dumps(badges))

######################## METHODS #############################################
def getUser(graph, cookie):
    """Returns a User model, built from the Facebook Graph API data.  
    """
    # Build User from Facebook Graph API ...
    profile = graph.get_object("me")
    try: # If the user has no location set, make the default "Earth"
        loc_id = fb_location_id=profile["location"]["id"]
        loc_name = fb_location_name=profile["location"]["name"]
    except KeyError:
        loc_id = "000000000000001"
        loc_name = "Earth"    
    user = models.User(key_name=str(profile["id"]),
                       fb_id=str(profile["id"]),
                       name=profile["name"],
                       fb_profile_url=profile["link"],
                       fb_location_id=loc_id,
                       fb_location_name=loc_name,
                       access_token=cookie["access_token"])
    user.put() 
    return user

def getGame(bgg_id, mid=None):
    """Returns a Game.  Looks for one in memcache, if not then creates one
    using the BGG XML API.
    """
    logging.info('########### getGame:: ####################################')
    if mid is None:
        self.redirect(500)
    game_cache = memcache.get(mid)
    game_url = BGG_XML_URI + bgg_id
    if game_cache is None:
        game = models.Game.get_by_key_name(mid)
        if game is None: # Game has never been stored, so build and store it.
            if bgg_id == '0' or bgg_id is None: # Call BGG XML API for match
                fb_game = getFBGame(mid)
                bgg_id = getBGGIDFromBGG(fb_game.game_name)
                if bgg_id is None:
                    self.redirect(500)
                    
            game_xml = models.GameXML.get_by_key_name(bgg_id)
            # Use BGG XML API to get Game data
            game_data = parseBGGXML(game_url)
            # Build Game from BGG data
            game = models.Game(key_name=mid,
                               mid=mid,
                               bgg_id=bgg_id,
                               bgg_img_url=game_data['image_url'],
                               bgg_thumbnail_url=game_data['thumbnail_url'],
                               name=game_data['name'],
                               description=game_data['description'],
                               year_published = game_data['year_published'],
                               min_players = game_data['min_players'],
                               playing_time = game_data['playing_time'],
                               age = game_data['age'],
                               publishers = game_data['publishers'],
                               artists = game_data['artists'],
                               designers = game_data['designers'],
                               expansions = game_data['expansions'],
                               categories = game_data['categories'],
                               mechanics = game_data['mechanics'],
                               subdomains = game_data['subdomains'])
            if game_xml is None:
                game_xml = models.GameXML(key_name=bgg_id, 
                                          xml=game_data['xml_text'])  
            else:
                game_xml.xml = game_data['xml_text']                 
            game.put() # Save Game
            game_xml.put() # Save GameXML       
            success = memcache.set(key=mid, 
                                   value=game, 
                                   time=432000) # expiration 5 days
            game_cache = game                                        
        else:
            game_xml = models.GameXML.get_by_key_name(bgg_id)
            # Use BGG XML API to get Game data
            game_data = parseBGGXML(game_url)
            # Build Game from BGG data            
            game.name = game_data['name']
            game.bgg_id = bgg_id
            game.bgg_thumbnail_url = game_data['thumbnail_url']            
            game.bgg_img_url = game_data['image_url']
            game.description = game_data['description']
            game.year_published = game_data['year_published']
            game.min_players = game_data['min_players']
            game.playing_time = game_data['playing_time']
            game.age = game_data['age']
            game.publishers = game_data['publishers']
            game.artists = game_data['artists']
            game.designers = game_data['designers']  
            game.expansions = game_data['expansions']
            game.categories = game_data['categories']
            game.mechanics = game_data['mechanics']
            game.subdomains = game_data['subdomains']
            game_xml.xml = game_data['xml_text']
            game.put() # Save Game
            game_xml.put() # Save GameXML
            success = memcache.set(key=mid, 
                                   value=game, 
                                   time=432000) # expiration 5 days
            game_cache = game        
    return game_cache

def parseBGGXML(bgg_game_url):
    """Returns a dictionary of game data retrieved from BGGs XML API.
    """
    result = urllib2.urlopen(bgg_game_url).read()
    xml = ElementTree.fromstring(result)
    decoded_result = result.decode("utf-8")
    xml_text = db.Text(decoded_result)
    bgg_data = {'name': findPrimaryName(xml),
                'description': xml.findtext(".//description"),
                'year_published': strToInt(xml.findtext(".//yearpublished")),
                'min_players': strToInt(xml.findtext(".//minplayers")),
                'max_players': strToInt(xml.findtext(".//maxplayers")),
                'playing_time': strToInt(xml.findtext(".//playingtime")),
                'age': strToInt(xml.findtext(".//age")),
                'publishers': 
                    buildDataList(xml.findall(".//boardgamepublisher")),
                'artists': buildDataList(xml.findall(".//boardgameartist")),
                'designers': 
                    buildDataList(xml.findall(".//boardgamedesigner")),  
                'expansions': 
                    buildDataList(xml.findall(".//boardgameexpansion")),
                'categories': 
                    buildDataList(xml.findall(".//boardgamecategory")),
                'mechanics': 
                    buildDataList(xml.findall(".//boardgamemechanic")),
                'subdomains': 
                    buildDataList(xml.findall(".//boardgamesubdomain")),
                'image_url': xml.findtext(".//image"),
                'thumbnail_url':xml.findtext(".//thumbnail"),
                'xml_text': xml_text}
    
    return bgg_data

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
    logging.info('############ getBGGIDFromBGG:: finding bgg_id ############')
    logging.info('########### game_name = ' + game_name + ' ###########')   
    game_url = BGG_XML_SEARCH + urllib2.quote(game_name)
    logging.info('########### game_url = ' + game_url + ' ###########') 
    result = urllib2.urlopen(game_url).read()
    xml = ElementTree.fromstring(result)
    bgg_id = xml.find("./boardgame").attrib['objectid']
    return bgg_id

def createCheckin(user, game_key, facebook=False):
    players = [user.key()] # A new Checkin has only one User
    # Create initial json data:
    # {'player': 
    #     {'name':name,'fb_id':fb_id},
    # 'badges': 
    #     [{'name':name,'img_url':img_url,'key_name':key_name},
    #      {'name':name,'img_url':img_url,'key_name':key_name}]
    # }
    player = {'name' : user.name, 'fb_id': user.fb_id}
    badge_entities = awardCheckinBadges(user, game_key)  
    badges=[]
    for b in badge_entities:
        logging.info('################ badge = ' +str(b)+ '##############')
        badge = {'name':b.name, 'img_url':b.img_url, 'key_name':b.key().name()}
        badges.append(badge)      
    json_dict = {'player': player, 'badges': badges}
    json = simplejson.dumps(json_dict)  
    checkin = models.Checkin(player=user, 
                             game=game_key, 
                             json=db.Text(json))    
    checkin.put()   
    user.last_checkin_time = datetime.datetime.now()
    user.put()

    return badges
    
def isCheckedIn(user):
    """Returns True if the User is checked into a Game with the check in grace
    period.   
    """
    time = datetime.datetime.now() - datetime.timedelta(0, CHECKIN_FREQUENCY)
    try:
        last_time = user.last_checkin_time
    except AttributeError:
        return False    
    if last_time is None:
        return False
    elif last_time > time:
        return True

def getUserCheckins(user):
    """Returns Checkins for a User.
    """
    # Data format:
    # [{'player': 
    #       {'name': name, 'fb_id': fb_id},
    #   'badges': 
    #       [{'name': name, 'id': id}, {'name': name, 'id': id}],
    #   'created': '3 minutes ago',
    #   'game': 
    #     {'name': name, 'mid': mid, "bgg_id": bgg_id, "bgg_img_url": url}
    #  }]    
    q_checkins = user.checkins
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin["created"] = c.created
        game = {"name": c.game.name, 
                "mid": c.game.mid, 
                "bgg_id": c.game.bgg_id, 
                "bgg_img_url": c.game.bgg_img_url}
        checkin["game"] = game
        checkins.append(checkin)
        logging.info('############# checkin ='+str(checkin)+' ##############')
    return checkins

def getGameCheckins(game):
    """Returns Checkins for a Game.
    """
    logging.info('##################### getGameCheckins ####################')    
    # Data format:
    # [{'players': 
    #       [{'name': name, 'fb_id': fb_id},{'name': name, 'fb_id': fb_id}],
    #   'badges': 
    #       [{'name': name, 'id': id}, {'name': name, 'id': id}],
    #   'time': '3 minutes ago'
    #  }]
    ref_checkins = game.checkins.order("-created") 
    checkins = [] 
    for c in ref_checkins:
        checkin = simplejson.loads(c.json)
        checkin["created"] = c.created
        checkins.append(checkin)
        logging.info('############### checkin ='+str(checkin)+' ############')
    return checkins   

def getLatestCheckins():
    """Returns lastest Checkins.
    """
    logging.info('##################### getLatestCheckins ##################')    
    # Data format:
    # [{'players': 
    #       [{'name': name, 'fb_id': fb_id},{'name': name, 'fb_id': fb_id}],
    #   'badges': 
    #       [{'name': name, 'id': id}, {'name': name, 'id': id}],
    #   'created': '3 minutes ago',
    #   'game': 
    #     {'name': name, 'mid': mid, "bgg_id": bgg_id, "bgg_img_url": url}
    #  }]
    q = models.Checkin.all()
    q.order("-created")
    q_checkins = q.fetch(14)  
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin["created"] = c.created
        game = {"name": c.game.name, 
                "mid": c.game.mid, 
                "bgg_id": c.game.bgg_id, 
                "bgg_img_url": c.game.bgg_img_url}
        checkin["game"] = game
        checkins.append(checkin)
        logging.info('############# checkin ='+str(checkin)+' ##############')
    return checkins

def parseGameAwards(game_award):
    """Returns a template iteratible list of game award winners.  
    """
    logging.info('##################### parseGameAwards ####################')       
    json_game_award = simplejson.loads(game_award.json_dump)
    games = []
    count = 0
    for r in json_game_award:
        name = r['name']
        year = r["!/award/award_honor/honored_for"]["year"]["value"]
        mid = r["mid"]
        bgg_id = r["key"]["value"]
        game = {}
        game["name"] = name
        game["year"] = year
        game["mid"] = mid
        game["bgg_id"] = bgg_id
        games.append(game)
    return games

def getFBUser(fb_id=None):
    """Returns a User for the given fb_id.
    """
    logging.info('##################### getUser ############################')        
    user = models.User.get_by_key_name(fb_id)
    return user

def awardCheckinBadges(user, game_key):
    """Returns any badges earned by a User.  Checks Checkins for badge
    triggers.  If any triggers are met, the Badges are awarded/saved.
    """
    createBadges()
    keys = []
    # Is this the first checkin for this Game?
    q = models.Checkin.all()
    q.filter("game =", game_key)  
    any_checkin = q.get()
    if any_checkin is None: keys.append(BADGE_KEY_GAME_CHECKIN_FIRST)    
    """
    # Award Badge for number of checkins
    checkin_count = user.checkin_count
    if checkin_count == 2:
        keys.append(BADGE_KEY_CHECKIN_A)   
    elif checking_count == 11:    
        keys.append(BADGE_KEY_CHECKIN_B)   
    elif checking_count == 21:    
        keys.append(BADGE_KEY_CHECKIN_C)   
    elif checking_count == 51:    
        keys.append(BADGE_KEY_CHECKIN_D)   
    elif checking_count == 101:    
        keys.append(BADGE_KEY_CHECKIN_E)   
    elif checking_count == 151:
        keys.append(BADGE_KEY_CHECKIN_F)   
    elif checking_count == 201:
        keys.append(BADGE_KEY_CHECKIN_G)   

    """
    # If checkins equal badge, add badge
    
    # is if first checkin to game?
    
    #
    if not keys: return None
    else:
        user.badges.extend(keys)
        user.put() 
        return db.Model.get(keys)

def createBadges():
    
    host = "http://localhost:8080"
    badgeA = models.Badge(key_name=BADGE_NAME_CHECKIN_COUNT_A,
                          name=BADGE_NAME_CHECKIN_COUNT_A,
                          img_url=host + BADGE_IMG_CHECKIN_COUNT_A)

    badgeB = models.Badge(key_name=BADGE_NAME_CHECKIN_COUNT_B,
                          name=BADGE_NAME_CHECKIN_COUNT_B,
                          img_url=host + BADGE_IMG_CHECKIN_COUNT_B)

    badgeC = models.Badge(key_name=BADGE_NAME_CHECKIN_COUNT_C,
                          name=BADGE_NAME_CHECKIN_COUNT_C,
                          img_url=host + BADGE_IMG_CHECKIN_COUNT_C)

    badgeFirst = models.Badge(key_name=BADGE_NAME_GAME_CHECKIN_FIRST,
                              name=BADGE_NAME_GAME_CHECKIN_FIRST,
                              img_url=host + BADGE_IMG_GAME_CHECKIN_FIRST)
    
    badgeA.put()                          
    badgeB.put()                          
    badgeC.put()                          
    badgeFirst.put() 
    return                         


    
##############################################################################
application = webapp.WSGIApplication([('/game', GameProfile),
                                     (r'/game(/m/.*)/(.*)', GameProfile),
                                     (r'/user/(.*)', UserProfile),
                                     ('/game-checkin', Checkin),
                                     (r'/admin/(.*)', Admin),
                                     (r'/.*', MainHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
