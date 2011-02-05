#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import os
import cgi
import freebase
import logging
import facebook
import models
import datetime
import re
import urllib2
import utils
from utils import strToInt
from utils import buildDataList
from utils import findPrimaryName

from settings import *
from urlparse import urlparse
from xml.etree import ElementTree 
from django.utils import simplejson
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

############################# REQUEST HANDLERS ############################### 
##############################################################################   
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
    """Provides Admin access to data-entry and initialization tasks.
    """
    def get(self, pswd=None):
        logging.info('################### Admin:: get() ####################')
        logging.info('################### pswd =' +pswd+ ' #################')        
        if pswd == "backyardchicken":
            badges = getBadges()
            image_upload_url = blobstore.create_upload_url('/upload/image')
            template_values = {
                'badges': badges,
                'image_upload_url': image_upload_url,
                'current_user': self.current_user,
                'facebook_app_id': FACEBOOK_APP_ID
            }  
            self.generate('base_admin.html', template_values)
        else: self.redirect(500)  
        
    def post(self, method=None):
        logging.info('################### Admin:: post() ###################')
        logging.info('################### method =' +method+' ##############')
        if method == "create-badges":
            createBadges()
        if method == "seed-games":
            taskqueue.add(url='/_ah/queue/seed-games')           
        if method == "build-games":
            buildGames()
        if method == "flush-cache":
            memcache.flush_all()    
        self.redirect('/admin/backyardchicken')  
    
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    """Uploads files to Blobstore.
    """
    def post(self, form=None):
        upload_files = self.get_uploads('file') 
        blob_info = upload_files[0]
        key_name = self.request.get('key_name')
        badge = models.Badge.get_by_key_name(key_name)
        if form == "image":
            badge.image = blob_info.key()
            badge.image_url = images.get_serving_url(blob_info.key())
        badge.put()   
        logging.info('################# badge.image = '+str(badge.image)+'################')    
        logging.info('################# badge.image.key = '+str(badge.image.key)+'################') 
        self.redirect('/admin/backyardchicken')  

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    """Serves Blobstore images.
    """
    def get(self, resource):
        resource = str(urllib2.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)

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
        game = getGame(self=self, mid=mid, bgg_id=bgg_id)
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
        # TODO: if BGGID is not on Freebase, then get it from BGG.
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
        badges = db.get(profile_user.badges)
        host = self.request.host # used for Facebook Like url 
        template_values = {
            'host': host,
            'badges': badges,
            'checkins': checkins,
            'profile_user': profile_user,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_user.html', template_values)

class Checkin(BaseHandler):
    """Accepts Checkin POSTs.
    """
    def post(self):
        logging.info('#################### Checkin::post ###################')
        user = self.current_user
        mid = self.request.get('mid')
        bgg_id = self.request.get('bgg_id')
        name = self.request.get('name')
        message = self.request.get('message')
        share = self.request.get('facebook')
        thumbnail = self.request.get('thumbnail')
        logging.info('#################### mid = '+mid+' ###################')
        logging.info('#################### bgg_id = '+bgg_id+' #############')
        logging.info('#################### name = '+name+' #################')
        logging.info('#################### message = '+message+' ###########')
        logging.info('#################### facebook = '+share+' ############')
        logging.info('#################### thumbnail = '+thumbnail+' #######')
        game_key = db.Key.from_path('Game', mid)
        game = models.Game.get(game_key)
        # Check user into game ...
        badges = createCheckin(user=user, game=game, share=share)
        # Share checkin on Facebook if requested ...
        if share.upper() == 'TRUE':# Announce checkin on Facebook Wall
            logging.info('#### posting to Facebook '+user.access_token+'####')
            attachment = {}
            description = utils.smart_truncate(game.description, length=300)
            url = 'http://www.supermeeple.com' + mid + '/' + bgg_id
            caption = "SuperMeeple: Board Game Database, Tools and Apps"
            attachment['caption'] = caption
            attachment['name'] = name
            attachment['link'] = url #url
            attachment['description'] = description   
            attachment['picture'] = thumbnail
            action_link = 'http://www.supermeeple.com'+str(mid)+'/'+str(bgg_id)
            action_name = "Check In!"
            actions = {"name": action_name, "link": action_link}
            attachment['actions'] = actions     
            results = facebook.GraphAPI(
               user.access_token).put_wall_post(message, attachment)
  
        return self.response.out.write(simplejson.dumps(badges))

class Page(MainHandler):
    """Returns content for meta pages.
    """   
    def get(self, page=None):
        path = ""
        if isFacebook(self.request.path):
            path = "facebook/fb_"            
        if page == "signup":
            template = path+"base_signup.html"
        elif page == "about":
            template = path+"base_about.html"    
        elif page == "contact":
            template = path+"base_contact.html"
        elif page == "rewards":
            template = path+"base_rewards.html"                           
        elif page == "terms":
            template = path+"base_terms.html"        
        else:
            template = path+"base_404.html"   
        logging.info("############### template ="+template+" ###############")    
        self.generate(template, {
                      'host': self.request.host_url, 
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})        

######################## METHODS #############################################
##############################################################################
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

def getFBUser(fb_id=None):
    """Returns a User for the given fb_id.
    """
    logging.info('##################### getUser ############################')        
    user = models.User.get_by_key_name(fb_id)
    return user

def getGame(self, bgg_id, mid=None):
    """Returns a Game.  Looks for one in memcache, if not then creates one
    using the BGG XML API.
    """
    logging.info('########### getGame:: ####################################')
    ##########################################################################
    # TODO: nested if statement is  . . . scary - could use a refactor!       #
    ##########################################################################
    if mid is None:
        self.redirect(500)
    game_cache = memcache.get(mid)
    game_url = BGG_XML_URI + bgg_id
    if game_cache is None:
        game = models.Game.get_by_key_name(mid)
        if game is None: # Game has never been stored, so build and store it.
            if bgg_id == '0' or bgg_id is None: # Call BGG XML API for match
                fb_game = getFBGame(mid)
                bgg_id = getBGGIDFromBGG(fb_game.name)
                if bgg_id is None:
                    self.redirect(500)
            logging.info('########## Found BGG ID! = '+bgg_id+' ############')        
            game_xml = models.GameXML.get_by_key_name(bgg_id)
            # Use BGG XML API to get Game data
            game_url = BGG_XML_URI + bgg_id # Remake url with new found bgg_id
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
    logging.info("########### parseBGGXML = "+bgg_game_url+" ###############")
    result = urllib2.urlopen(bgg_game_url).read()
    try:
        xml = ElementTree.fromstring(result)
    except Exception:
        logging.info("################## error parsing BGG #################")
        return None  
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
        "value" : None,
        "optional": True
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
        logging.info('########## bgg_id = ' +game_ids["bgg_id"]+' ##########')  
        return game_ids
    else:
        game_ids = {"bgg_id":None, "mid":result.mid}
        logging.info('#################### bgg_id = None ###################')         
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
    logging.info('########### bgg_id = ' + str(bgg_id) + ' ###########') 
    return bgg_id

def createCheckin(user, game, share=False):
    logging.info('################### createCheckin() ######################')
    players = [user.key()] # A new Checkin has only one User
    # Create initial json data:
    # {'player': 
    #     {'name':name,'fb_id':fb_id},
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
    # }
    player = {'name' : user.name, 'fb_id': user.fb_id}
    user.checkin_count += 1
    game.checkin_count += 1
    badge_entities = awardCheckinBadges(user, game.key())  
    badges=[]
    if badge_entities is not None:
        for b in badge_entities:
            logging.info('######## badge.name = ' +str(b.name)+ '###########')
            logging.info('######## badge.image_url= ' +str(b.image_url)+ '##')
            badge = {'name':b.name, 
                     'image_url': b.image_url,
                     'key_name':b.key().name()}
            badges.append(badge)      
    json_dict = {'player': player, 'badges': badges}
    json = simplejson.dumps(json_dict)  
    checkin = models.Checkin(player=user, 
                             game=game.key(), 
                             json=db.Text(json))    
    
    # TODO: either batch put, and run in Transaction or Task.
    checkin.put()   
    user.last_checkin_time = datetime.datetime.now()
    user.put()
    game.put()
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
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
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
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
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
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
    #   'created': '3 minutes ago',
    #   'game': 
    #     {'name': name, 'mid': mid, "bgg_id": bgg_id, "bgg_img_url": url}
    #  }]
    q = models.Checkin.all()
    q.order("-created")
    q_checkins = q.fetch(10)  
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin["created"] = c.created
        game = {"name": c.game.name, 
                "mid": c.game.mid, 
                "bgg_id": c.game.bgg_id, 
                "bgg_img_url": c.game.bgg_thumbnail_url}
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

def awardCheckinBadges(user, game_key):
    """Returns any badges earned by a User.  Checks Checkins for badge
    triggers.  If any triggers are met, the Badges are awarded/saved.
    """
    keys = []
    ######## AWARD 1ST CHECKIN ###############################################
    q = models.Checkin.all()
    q.filter("game =", game_key)  
    any_checkin = q.get()
    if any_checkin is None: 
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_1ST))   
        
    ######## AWARD CHECKIN LEVELS ############################################
    checkin_count = user.checkin_count
    if checkin_count == 2:
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_1))   
    elif checkin_count == 8:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_2))  
    elif checkin_count == 16:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_3)) 
    elif checkin_count == 26:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_4))
    elif checkin_count == 38:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_5))
    elif checkin_count == 52:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_6))
    elif checkin_count == 68:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_7))
    elif checkin_count == 86:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_8))  
    elif checkin_count == 106:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_9))
    elif checkin_count == 128:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_10))                                                       

    ######## AWARD CHARE LEVELS ##############################################
    share_count = user.share_count
    if share_count == 2:
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_1))   
    elif share_count == 8:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_2))  
    elif share_count == 16:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_3)) 
    elif share_count == 26:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_4))
    elif share_count == 38:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_5))
    elif share_count == 52:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_6))
    elif share_count == 68:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_7))
    elif share_count == 86:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_8))  
    elif share_count == 106:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_9))
    elif share_count == 128:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_10))

    ######## AWARD BADGES ############################################
    # TODO: other badge awards go here . . .
    
    if not keys: return None
    else:
        user.badges.extend(keys)
        user.put() 
        return db.Model.get(keys)

def getBadges():
    """Returns all Badge Entities in the Datastore"""
    return models.Badge.all().fetch(500)
    
def createBadges():
    updated = []    
    for b in BADGES:
        badge = models.Badge(key_name=b, name=b, description=b)
        updated.append(badge)
   
    db.put(updated)
    return None                      

def isFacebook(path):
    """Returns True if request is from a Facebook iFrame, otherwise False.
    """
    if re.search(r".facebook\.*", path): # match a Facebook apps uri
        logging.info("############### facebook detected! ###############")
        return True
    else:
        logging.info("############### facebook NOT detected! ###########")        
        return False

def buildGames():
    logging.info("################## main.py:: buildGames() ################")   
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
    count = 0
    for r in results:
        logging.info("################ result:: "+str(r)+" #################")    
        mid = r.mid
        bgg_id = r.key.value
        taskqueue.add(url='/_ah/queue/build-games', 
                      params={'bgg_id': bgg_id, 'mid': mid})
        
        count +=1
        if count > 300: return True              
  
    return True  

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
    count = 0
    for r in results:
        logging.info("################ result:: "+str(r)+" #################")    
        mid = r.mid
        bgg_id = r.key.value
        taskqueue.add(url='/_ah/queue/seed-games', 
                      params={'bgg_id': bgg_id, 'mid': mid})
        
  
    return True             
##############################################################################
##############################################################################
application = webapp.WSGIApplication([(r'/page/(.*)', Page),
                                      ('/game', GameProfile),
                                      (r'/game(/m/.*)/(.*)', GameProfile),
                                      (r'/user/(.*)', UserProfile),
                                      ('/game-checkin', Checkin),
                                      (r'/admin/(.*)', Admin),
                                      (r'/upload/(.*)', UploadHandler),
                                      (r'/serve/([^/]+)?', ServeHandler),
                                      (r'/.*', MainHandler)],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
