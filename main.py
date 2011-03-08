#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import os
import cgi
import checkinbase
import freebase
import logging
import facebook
import gamebase
import models
import operator
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
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import deferred
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
                    user = createUser(
                            facebook.GraphAPI(cookie["access_token"]),
                            cookie)
                # Update the user data if it has changed.
                # TODO: if the access_token has changed, may need to
                # re-solicit permissions.            
                else:
                    user = updateUser(user,
                            facebook.GraphAPI(cookie["access_token"]),
                            cookie)    
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
        logging.info('######### badge.image = '+str(badge.image)+'##########')    
        logging.info('######### badge.image.key = '+str(badge.image.key)+'##') 
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
                            "namespace":"/user/pak21/boardgamegeek/boardgame",
                            "value":None
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
        game = gamebase.getGame(mid=mid, bgg_id=bgg_id)
        checkins = getGameCheckins(game, 4)
        high_scores = checkinbase.getGameHighScores(game, 4)
        host = self.request.host # used for Facebook Like url 
        checked_in = isCheckedIn(user)   
        admin = users.is_current_user_admin()  
        template_values = {
            'admin': admin,
            'checked_in': checked_in,
            'host': host,
            'game': game,
            'checkins': checkins,
            'high_scores': high_scores,
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
        checkins = getUserCheckins(profile_user, 10)
        scores = checkinbase.getScoresFromFriends(profile_user, 10)
        badges = db.get(profile_user.badges)
        host = self.request.host # used for Facebook Like url 
        template_values = {
            'host': host,
            'badges': badges,
            'checkins': checkins,
            'scores': scores,
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
        badges = createCheckin(user=user, game=game, 
                               message=message, share=share)
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

class GameLog(BaseHandler):
    """Display and creates a GameLog.
    """
    def get(self, checkin_id):
        logging.info('#################### GameLog::get ####################')        
        checkin = models.Checkin.get_by_id(strToInt(checkin_id)) 
        game = checkin.game
        checkin_json = simplejson.loads(checkin.json)
        checkin_json['created'] = checkin.created
        checkin_json['id'] = str(checkin.key().id())
        logging.info('################# '+str(checkin_json)+' ##############')            
        user = self.current_user # this is the logged in User 
        result = facebook.GraphAPI(
            user.access_token).get_connections('me', 'friends')
        fb_data = result["data"]
        friends = []
        for f in fb_data:
            friends.append({'value':f['id'], 'label':f['name']})
        template_values = {
            'friends': simplejson.dumps(friends),
            'checkin': checkin_json,
            'game': game,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_gamelog.html', template_values)
        
    def post(self, checkin_id):
        """Builds GameLog and Scores for a corresponding Checkin.  The
        Checkin 'id' is used as the GameLog 'key_name'.  Users can add any
        Players they want to their GameLog, but only Players with an fb_id
        will be used to create References to Users and Scores.  However,
        Players without an fb_id will be included in the list of Players
        updated to Checkin.json.     
        """
        logging.info('############# GameLog::post('+checkin_id+') ##########')
        game_log = models.GameLog.get_by_key_name(checkin_id)  
        if game_log: return # game_log already exists!
        checkin = models.Checkin.get_by_id(strToInt(checkin_id))
        user = self.current_user
        # Read and organize data ...
        note = self.request.get('note')
        mid = self.request.get('mid')  
        winner = self.request.get('winner')
        logging.info('############# note = '+note+' ##########')
        logging.info('############# mid = '+mid+' ##########') 
        game_key = db.Key.from_path('Game', mid)         
        scores = [] 
        player_keys = []
        entities = []
        count = 1
        while (count < 9):
            player_name = self.request.get('player-name-'+str(count))
            if player_name:
                player_id = self.request.get('player-id-'+str(count)) 
                points = self.request.get('player-score-'+str(count))

                if winner == 'player-name-'+str(count):
                    win = True
                else: win = False    
                score = {"name":player_name,
                         "fb_id":player_id,
                         "points":points,
                         "winner":win}
                logging.info('#### score '+str(count)+' '+str(score)+' ###')
                scores.append(score)                    
                if player_id: # Only Facebook Players ...
                    player_key = db.Key.from_path('User', player_id)
                    player = models.User.get(player_key)
                    # If the player has never logged on, create them
                    if player is None:
                        player = createLiteUser(player_name, player_id)
                        entities.append(player)
                    player_keys.append(player_key)
                    # Create Score ...
                    entity = models.Score(game=game_key,
                                          player=player_key,
                                          gamelog_id=strToInt(checkin_id),
                                          points=strToInt(points),
                                          win=win, 
                                          author=user)
                    entities.append(entity)
            count += 1
            
        # Update Checkin with JSON string of Scores ...    
        game_log_json = {'scores':scores, 'note':note}    
        checkin_json_dict = simplejson.loads(checkin.json)
        checkin_json_dict['gamelog'] = game_log_json
        checkin_json_txt = simplejson.dumps(checkin_json_dict)
        checkin.json = db.Text(checkin_json_txt)
        entities.append(checkin)
        
        # Create a new GameLog ...
        game_log = models.GameLog(key_name=checkin_id,
                                  game=game_key,
                                  checkin=checkin,
                                  note=note,
                                  players=player_keys)
        entities.append(game_log)
        
        # Update User's score count ...
        user.score_count += 1
        entities.append(user)
                
        # Save all entities
        db.put(entities)
      
        # Share checkin on Facebook if requested ...
        share = self.request.get('facebook')
        deferred.defer(checkinbase.shareGameLog, 
                       share, 
                       user, 
                       simplejson.loads(checkin.json))

        return self.response.out.write(simplejson.dumps(game_log_json))

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

class TestHandler(BaseHandler):
    """Testing.
    """
    def get(self, checkin_id):
        logging.info('#################### TestHandler::get ################')        
        user = self.current_user # this is the logged in User 
        access_token = user.access_token
        result = facebook.GraphAPI(
            user.access_token).get_connections('me', 'friends')
        fb_data = result["data"]
        friends = []
        for f in fb_data:
            friends.append({'value':f['id'], 'label':f['name']})
        template_values = {
            'friends': simplejson.dumps(friends),
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_test.html', template_values)


######################## METHODS #############################################
##############################################################################
def createUser(graph, cookie):
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
  
def updateUser(user, graph, cookie):
    """Returns a User model, updated from the Facebook Graph API data.  
    """
    logging.info('###################### updateUser ########################')
    props = user.properties() # This is what's in the Datastore
    profile = graph.get_object("me") # This is what Facebook has
    new_access_token = cookie["access_token"]
    new_profile_url = profile["link"]
    try: # If the user has no location set, make the default "Earth"
        new_loc_id = fb_location_id=profile["location"]["id"]
        new_loc_name = fb_location_name=profile["location"]["name"]
    except KeyError:
        new_loc_id = "000000000000001"
        new_loc_name = "Earth"    
    update = False
    # Compare properties and only update if things have changed ...
    if new_profile_url != props['fb_profile_url']:
        user.fb_profile_url = new_profile_url
        update = True
    if new_loc_id != props['fb_location_id']:
        user.fb_location_id = new_loc_id
        update = True
    if new_loc_name != props['fb_location_name']:
        user.fb_location_name = new_loc_name
        udpate = True
    if new_access_token != props['access_token']:    
        user.access_token = new_access_token
        update = True
    if update == True:
        user.put() 
    return user
    
def createLiteUser(name, fb_id):
    """Returns a new User model, built using the minumum data requirements.
    """
    logging.info('########## createLiteUser('+name+', '+fb_id+') ###########')
    user = models.User(key_name=fb_id,
                       fb_id=fb_id,
                       name=name)    
    return user

def getFBUser(fb_id=None):
    """Returns a User for the given fb_id.
    """
    logging.info('##################### getUser ############################')        
    user = models.User.get_by_key_name(fb_id)
    return user

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

def createCheckin(user, game, message, share=False):
    logging.info('################### createCheckin() ######################')
    players = [user.key()] # A new Checkin has only one User
    # Create initial json data:
    # {'player': 
    #     {'name':name,'fb_id':fb_id},
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
    #  'message': message,
    #  'game':
    #     {'name':name,'mid':mid,'bgg_id':bgg_id,'bgg_img_url':bgg_img_url}
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
    game_data = {'name': game.name, 
                 'mid': game.mid, 
                 'bgg_id': game.bgg_id, 
                 'bgg_thumbnail_url': game.bgg_thumbnail_url}          
    json_dict = {'player': player, 
                 'badges': badges, 
                 'message': message, 
                 'game':game_data}
    json = simplejson.dumps(json_dict)  
    checkin = models.Checkin(player=user, 
                             game=game.key(), 
                             message=message,
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

def getUserCheckins(user, count=10):
    """Returns Checkins for a User.
    """
    # Data format:
    # [{'id':id,    
    #   'player': 
    #       {'name': name, 'fb_id': fb_id},
    #   'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
    #   'created': '3 minutes ago',
    #   'game': 
    #     {'name': name, 'mid': mid, "bgg_id": bgg_id, "bgg_img_url": url},
    #   'message': 'message    
    #   'gamelog':
    #     {'note':note, 
    #      [{'winner':boolean, 'points':int, 'name':player, 'fb_id':fb_id},
    #       {'winner':boolean, 'points':int, 'name':player, 'fb_id':fb_id}]
    #     } 
    #  }]    
    q_checkins = user.checkins.order('-created').fetch(count)
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin['created'] = c.created
        checkin['id'] = str(c.key().id())
        checkins.append(checkin)
        logging.info('############# checkin ='+str(checkin)+' ##############')
    return checkins

def getGameCheckins(game, count=10):
    """Returns Checkins for a Game.
    """
    logging.info('##################### getGameCheckins ####################')    
    # Data format:
    # [{'id':id,     
    #   'player': 
    #       {'name': name, 'fb_id': fb_id},
    #   'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
    #   'created': '3 minutes ago'
    #   'message': 'message    
    #  }]
    ref_checkins = game.checkins.order('-created').fetch(count)
    checkins = [] 
    for c in ref_checkins:
        checkin = simplejson.loads(c.json)
        checkin['created'] = c.created
        checkin['id'] = str(c.key().id())
        checkins.append(checkin)
        logging.info('############### checkin ='+str(checkin)+' ############')
    return checkins   

def getLatestCheckins(count=10):
    """Returns lastest Checkins.
    """
    logging.info('##################### getLatestCheckins ##################')    
    # Data format:
    # [{'id':id,     
    #   'player':
    #       {'name': name, 'fb_id': fb_id},
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
    #   'created': '3 minutes ago',
    #   'game': 
    #     {'name': name, 'mid': mid, "bgg_id": bgg_id, "bgg_img_url": url},
    #    'message': 'message
    #  }]
    q = models.Checkin.all()
    q.order('-created')
    q_checkins = q.fetch(count)  
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin['created'] = c.created
        checkin['id'] = str(c.key().id())
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
        year = r['!/award/award_honor/honored_for']['year']['value']
        mid = r['mid']
        bgg_id = r['key']['value']
        game = {}
        game['name'] = name
        game['year'] = year
        game['mid'] = mid
        game['bgg_id'] = bgg_id
        games.append(game)
    return games

def awardCheckinBadges(user, game_key):
    """Returns any badges earned by a User.  Checks Checkins for badge
    triggers.  If any triggers are met, the Badges are awarded/saved.
    """
    keys = []
    ######## AWARD 1ST CHECKIN ###############################################
    q = models.Checkin.all()
    q.filter('game =', game_key)  
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
                                      (r'/game-log/(.*)', GameLog),
                                      (r'/upload/(.*)', UploadHandler),
                                      (r'/serve/([^/]+)?', ServeHandler),
                                      (r'/test/(.*)', TestHandler),
                                      (r'/.*', MainHandler)],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
