# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

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
        logging.info(TRACE+' BaseHandler:: current_user()')
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                token = cookie[TOKEN]
                logging.info(TRACE+' access_token = '+token)
                user = models.User.get_by_key_name(cookie["uid"])
                graph = facebook.GraphAPI(token)                
                if not user: # Build a User
                    user = createUser(graph, cookie)
                # Update the user data if it has changed.
                # TODO: if the access_token has changed, may need to
                # re-solicit permissions.            
                else:
                    user = updateUser(user, graph, cookie)    
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
        logging.info(TRACE+'UploadHandler:: post()')         
        upload_files = self.get_uploads('file') 
        blob_info = upload_files[0]
        key_name = self.request.get('key_name')
        badge = models.Badge.get_by_key_name(key_name)
        if form == "image":
            badge.image = blob_info.key()
            badge.image_url = images.get_serving_url(blob_info.key())
        if form == "banner":
            badge.banner = blob_info.key()
            badge.banner_url = images.get_serving_url(blob_info.key())            
        badge.put()   
        logging.info(TRACE+'UploadHandler:: badge.image = '+str(badge.image))    
        logging.info(TRACE+'UploadHandler:: badge.image.key = '+str(badge.image.key)) 
        self.redirect('/admin/')  
                                                
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
        logging.info(TRACE+'MainHandler:: get()')
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
        
        checkins = checkinbase.getLatestCheckins()    

        current_user = self.current_user  
        if current_user is not None:
            my_checkins = checkinbase.getUserCheckins(current_user, 4) 
        else: 
            my_checkins = None      
        
        template_values = {
            'checkins': checkins,
            'my_checkins': my_checkins,
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
        logging.info(TRACE+'GameProfile:: get()')
        user = self.current_user
        game = gamebase.getGame(mid=mid, bgg_id=bgg_id)
        checkins = checkinbase.getGameCheckins(game, 4)
        high_scores = checkinbase.getGameHighScores(game, 4)
        host = self.request.host # used for Facebook Like url 
        checked_in = checkinbase.isCheckedIn(user)   
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
        logging.info(TRACE+'GameProfile:: post()')
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
        logging.info(TRACE+'UserProfile:: get()')
        user = self.current_user # this is the logged in User
        profile_user = getFBUser(user_fb_id)
        checkins = checkinbase.getUserCheckins(profile_user, 10)
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
        logging.info(TRACE+'Checkin:: post()')
        user = self.current_user
        mid = self.request.get('mid')
        bgg_id = self.request.get('bgg_id')
        name = self.request.get('name')
        message = self.request.get('message')
        share = self.request.get('facebook')
        thumbnail = self.request.get('thumbnail')
        logging.info(TRACE+'Checkin:: mid = '+mid)
        logging.info(TRACE+'Checkin:: bgg_id = '+bgg_id)
        logging.info(TRACE+'Checkin:: name = '+name)
        logging.info(TRACE+'Checkin:: message = '+message)
        logging.info(TRACE+'Checkin:: facebook = '+share)
        logging.info(TRACE+'Checkin:: thumbnail = '+thumbnail)
        game_key = db.Key.from_path('Game', mid)
        game = models.Game.get(game_key)
        # Check user into game ...
        checkin = checkinbase.createCheckin(user=user, game=game, 
                                            message=message, share=share)
                                            
        # Share checkin on Facebook if requested ...
        if share.upper() == 'TRUE':# Announce checkin on Facebook Wall
            logging.info(TRACE+'Checkin:: posting to Facebook '+user.access_token)
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
               
        badges = checkin['badges']
        return self.response.out.write(simplejson.dumps(badges))

class GameLog(BaseHandler):
    """Display and creates a GameLog.
    """
    def get(self, checkin_id):
        logging.info(TRACE+'GameLog:: get()')        
        checkin = models.Checkin.get_by_id(strToInt(checkin_id)) 
        game = checkin.game
        checkin_json = simplejson.loads(checkin.json)
        checkin_json['created'] = checkin.created
        checkin_json['id'] = str(checkin.key().id())
        logging.info(TRACE+'GameLog:: '+str(checkin_json))            
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
        logging.info(TRACE+'GameLog:: post('+checkin_id+')')
        game_log_json = checkinbase.createGameLog(self, checkin_id)
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
        logging.info(TRACE+'Page:: template = '+template)    
        self.generate(template, {
                      'host': self.request.host_url, 
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})        

class TestHandler(BaseHandler):
    """Testing.
    """
    def get(self, checkin_id):
        logging.info(TRACE+'TestHandler:: get()')        
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
        loc_id = profile["location"]["id"]
        loc_name = profile["location"]["name"]
    except KeyError:
        loc_id = "000000000000001"
        loc_name = "Earth"    
    user = models.User(key_name=str(profile["id"]),
                       fb_id=str(profile["id"]),
                       name=profile["name"],
                       fb_profile_url=profile["link"],
                       fb_location_id=loc_id,
                       fb_location_name=loc_name,
                       access_token=cookie[TOKEN])
    user.put() 
    return user
  
def updateUser(user, graph, cookie):
    """Returns a User model, updated from the Facebook Graph API data.  
    """
    logging.info(TRACE+' updateUser()')
    access_token = cookie[TOKEN]
    logging.info(TRACE+' access_token = '+access_token)    
    props = user.properties() # This is what's in the Datastore
    profile = graph.get_object("me") # This is what Facebook has
    new_profile_url = profile["link"]  
    try: # If the user has no location set, make the default "Earth"
        new_loc_id = profile["location"]["id"]
        new_loc_name = profile["location"]["name"]
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
    if access_token != props[TOKEN]:    
        user.access_token = access_token
        update = True
    if update == True:
        user.put() 
    return user
    
def createLiteUser(name, fb_id):
    """Returns a new User model, built using the minumum data requirements.
    """
    logging.info(TRACE+' createLiteUser('+name+', '+fb_id+')')
    user = models.User(key_name=fb_id,
                       fb_id=fb_id,
                       name=name)    
    return user

def getFBUser(fb_id=None):
    """Returns a User for the given fb_id.
    """
    logging.info(TRACE+' getFBUser()')        
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
        logging.info(TRACE+'getBGGIDFromFB():: bgg_id = ' +game_ids["bgg_id"])  
        return game_ids
    else:
        game_ids = {"bgg_id":None, "mid":result.mid}
        logging.info(TRACE+'getBGGIDFromFB():: bgg_id = None')         
        return game_ids   
        
def getBGGIDFromBGG(game_name):
    """Returns the Board Game Geek Game ID from Board Game Geek.    
    """
    logging.info(TRACE+'getBGGIDFromBGG():: finding bgg_id')
    logging.info(TRACE+'getBGGIDFromBGG():: game_name = ' + game_name)   
    game_url = BGG_XML_SEARCH + urllib2.quote(game_name)
    logging.info(TRACE+'getBGGIDFromBGG():: game_url = ' + game_url) 
    result = urllib2.urlopen(game_url).read()
    xml = ElementTree.fromstring(result)
    bgg_id = xml.find("./boardgame").attrib['objectid']
    logging.info(TRACE+'getBGGIDFromBGG():: bgg_id = ' + str(bgg_id)) 
    return bgg_id

def parseGameAwards(game_award):
    """Returns a template iteratible list of game award winners.  
    """
    logging.info(TRACE+'parseGameAwards()')       
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

def isFacebook(path):
    """Returns True if request is from a Facebook iFrame, otherwise False.
    """
    if re.search(r".facebook\.*", path): # match a Facebook apps uri
        logging.info(TRACE+'isFacebook():: facebook detected!')
        return True
    else:
        logging.info(TRACE+'isFacebook():: facebook NOT detected!')        
        return False
          
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
