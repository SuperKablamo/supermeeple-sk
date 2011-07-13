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

from model import user
from model import game
from settings import *
from utils import strToInt
from utils import buildDataList
from utils import findPrimaryName

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

from urlparse import urlparse
from xml.etree import ElementTree

############################# REQUEST HANDLERS ############################### 
##############################################################################   
class BaseHandler(webapp.RequestHandler):
    '''Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    '''
    @property
    def current_user(self):
        _trace = TRACE+'BaseHander:: current_user() '
        logging.info(_trace)
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                token = cookie[TOKEN]
                logging.info(_trace+'access_token = '+token)
                _user = models.User.get_by_key_name(cookie["uid"])
                graph = facebook.GraphAPI(token)                
                if not user: # Build a User
                    _user = user.createUser(graph, cookie)
                # Update the user data if it has changed.
                # If the user has deauthorized, and is active=False, then
                # user will need to re-solicit permissions.            
                else:
                    _user = user.updateUser(_user, graph, cookie)    
                self._current_user = _user
        return self._current_user
            
    def generate(self, template_name, template_values):
        template.register_template_library('templatefilters')
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, 
                            os.path.join('templates', template_name))

        self.response.out.write(template.render(path, 
                                                template_values, 
                                                debug=DEBUG))
                                            
    def error(self, code):
        '''Overide RequestHandler.error to return custom error templates.
        '''
        self.response.clear()
        self.response.set_status(code)
        template_name = str(code)+'.html'
        self.generate(template_name, None)     

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    '''Uploads files to Blobstore.
    '''
    def post(self, form=None):
        _trace = TRACE+'UploadHandler:: post() '
        logging.info(_trace)
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
        logging.info(_trace+'badge.image = '+str(badge.image))    
        logging.info(_trace+'badge.image.key = '+str(badge.image.key)) 
        self.redirect('/admin/')  
                                                
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    '''Serves Blobstore images.
    '''
    def get(self, resource):
        resource = str(urllib2.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)

class MainHandler(BaseHandler):
    '''Return content for index.html.     
    '''
    def get(self):
        _trace = TRACE+'MainHandler:: get() '
        logging.info(_trace)
        spiel_id = SPIEL_ID
        meeples_id = MEEPLES_ID
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
                                                    json=json_dump_text)
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
                                                      json=json_dump_text)
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
    '''Returns a Game data.
    
    GET - uses FB and BGG ids to build Game data for display. FB and BGG are
    queried for data, persisted to the Datastore (if new or updated), and the
    data is passed to HTML for display.
    
    POST - uses game_id to look up a Game on Freebase.  Then redirects to GET 
    in order to display Game Profile.  
    '''
    # Direct linking to Game Profile
    def get(self, mid=None, bgg_id=None):
        _trace = TRACE+'GameProfile:: get() '
        logging.info(_trace)
        user = self.current_user
        _game = game.getGame(mid=mid, bgg_id=bgg_id)
        if _game is None:
            self.error(404)
            return            
        checkins = checkinbase.getGameCheckins(_game, 4)
        high_scores = checkinbase.getGameHighScores(_game, 4)
        host = self.request.host # used for Facebook Like url 
        checked_in = checkinbase.isCheckedIn(user)   
        admin = users.is_current_user_admin()  
        template_values = {
            'admin': admin,
            'checked_in': checked_in,
            'host': host,
            'game': _game,
            'checkins': checkins,
            'high_scores': high_scores,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_game.html', template_values) 

    # Game search POST
    def post(self):
        _trace = TRACE+'GameProfile:: post() '
        logging.info(_trace)
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
    '''Returns content for User Profile pages.
    '''
    def get(self, user_fb_id=None):
        logging.info(TRACE+'UserProfile:: get()')
        user = self.current_user # this is the logged in User
        profile_user = getFBUser(user_fb_id)
        if profile_user is None:
            self.error(404)
            return
        checkins = checkinbase.getUserCheckins(profile_user, 10)
        scores = checkinbase.getScoresFromFriends(profile_user, 10)
        host = self.request.host # used for Facebook Like url 
        badge_log = checkinbase.getBadgeLog(profile_user)
        template_values = {
            'host': host,
            'checkins': checkins,
            'scores': scores,
            'profile_user': profile_user,
            'badge_log': badge_log,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_user.html', template_values)
        
    def post(self, user_fb_id=None):
        logging.info(TRACE+'UserProfile:: post()')
        user = self.current_user # this is the logged in User
        profile_user = getFBUser(user_fb_id)
        profile_user.welcomed = True
        db.put(profile_user)
        return None     

class Checkin(BaseHandler):
    '''Accepts Checkin POSTs.
    '''
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
                                            
        # Share gamelog on Facebook if requested ...
        if share.upper() == 'TRUE':
            deferred.defer(checkinbase.shareCheckin, user, game)        
               
        badges = checkin['badges']
        return self.response.out.write(simplejson.dumps(badges))

class GameLog(BaseHandler):
    '''Display and creates a GameLog.
    '''
    def get(self, checkin_id):
        logging.info(TRACE+'GameLog:: get()')        
        checkin = models.Checkin.get_by_id(strToInt(checkin_id)) 
        if checkin is None:
            self.error(404)
            return
        game = checkin.game
        checkin_json = simplejson.loads(checkin.json)
        checkin_json['created'] = checkin.created
        checkin_json['id'] = str(checkin.key().id())
        logging.info(TRACE+'GameLog:: '+str(checkin_json))            
        user = self.current_user # this is the logged in User 
        if user is not None:
            result = facebook.GraphAPI(
                user.access_token).get_connections('me', 'friends')
            
            fb_data = result["data"]
            friends = []
            for f in fb_data:
                friends.append({'value':f['id'], 'label':f['name']})
            
            friends = simplejson.dumps(friends)
        else:
            user = None
            friends = None
            
        template_values = {
            'friends': friends,
            'checkin': checkin_json,
            'game': game,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_gamelog.html', template_values)
        
    def post(self, checkin_id):
        '''Builds GameLog and Scores for a corresponding Checkin.  The
        Checkin 'id' is used as the GameLog 'key_name'.  Users can add any
        Players they want to their GameLog, but only Players with an fb_id
        will be used to create References to Users and Scores.  However,
        Players without an fb_id will be included in the list of Players
        updated to Checkin.json.     
        '''
        logging.info(TRACE+'GameLog:: post('+checkin_id+')')
        game_log_json = checkinbase.createGameLog(self, checkin_id)
        self.redirect('/game-log/'+checkin_id)

class Page(MainHandler):
    '''Returns content for meta pages.
    '''   
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
        #elif page == "badges":
        #    template = path+"base_badges.html" 
        else:
            self.error(404)
            return 
        logging.info(TRACE+'Page:: template = '+template)    
        self.generate(template, {
                      'host': self.request.host_url, 
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})        

class TestHandler(BaseHandler):
    '''Display and creates a GameLog.
    '''
    def get(self, checkin_id):
        logging.info(TRACE+'GameLog:: get()')        
        checkin = models.Checkin.get_by_id(strToInt(checkin_id)) 
        if checkin is None:
            self.error(404)
            return
        game = checkin.game
        checkin_json = simplejson.loads(checkin.json)
        checkin_json['created'] = checkin.created
        checkin_json['id'] = str(checkin.key().id())
        logging.info(TRACE+'GameLog:: '+str(checkin_json))            
        user = self.current_user # this is the logged in User 
        if user is not None:
            result = facebook.GraphAPI(
                user.access_token).get_connections('me', 'friends')
            
            fb_data = result["data"]
            friends = []
            for f in fb_data:
                friends.append({'value':f['id'], 'label':f['name']})
            
            friends = simplejson.dumps(friends)
        else:
            user = None
            friends = None
            
        template_values = {
            'friends': friends,
            'checkin': checkin_json,
            'game': game,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate('base_test.html', template_values)

######################## METHODS #############################################
##############################################################################


def getIDsFromFB(game_id):
    '''Returns the Board Game Geek Game ID and Freebase MID from Freebase.    
    '''
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
    '''Returns the Board Game Geek Game ID from Board Game Geek.    
    '''
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
    '''Returns a template iteratible list of game award winners.  
    '''
    logging.info(TRACE+'parseGameAwards()')       
    json_game_award = simplejson.loads(game_award.json)
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
    '''Returns True if request is from a Facebook iFrame, otherwise False.
    '''
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
                                      (r'/user/(.*)/.*', UserProfile),
                                      (r'/user/(.*)', UserProfile),
                                      ('/game-checkin', Checkin),
                                      (r'/game-log/(.*)', GameLog),
                                      (r'/upload/(.*)', UploadHandler),
                                      (r'/serve/([^/]+)?', ServeHandler),
                                      (r'/test/(.*)', TestHandler),
                                      (r'/.*', MainHandler)],
                                       debug=False)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
