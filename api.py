# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# api.py defines Handlers and Methods for providing API access to 
# SuperMeeple.com.
#
# ============================================================================

############################# SK IMPORTS #####################################
############################################################################## 
import checkinbase
import gamebase
import models
import utils

from settings import *

############################# GAE IMPORTS ####################################
##############################################################################
import datetime
import logging
import os
import urllib2

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

############################# CONSTANTS ######################################
##############################################################################
API200 = {"status": "200 OK", "code": "/api/status/ok"}
API404 = {"status": "404 Not Found", "code": "/api/status/error"}
API500 = {"status": "500 Internal Server Error", "code": "/api/status/error"}

############################# REQUEST HANDLERS ############################### 
##############################################################################
class APICheckin(webapp.RequestHandler):
    """Provides API access to Checkin data.  Responses are in JSON.
    """
    def get(self, method):
        logging.info(TRACE+'APICheckin:: get()')
        if method == "latest": 
            fb_id = self.request.get('fb_id')
            time_since = utils.strToInt(self.request.get('time_since'))
            limit = utils.strToInt(self.request.get('limit'))
            if time_since is None: time_since = 0 # Default to since 1970
            if limit is 0: limit = 10 # Default to a limit of 10
            if fb_id != '':
                logging.info(TRACE+'VALUE fb_id = ' +fb_id)                
                r = getLatestUserCheckins(limit, time_since, fb_id)
            else:    
                r = getLatestCheckins(limit, time_since)
        else: r = API404
        return self.response.out.write(simplejson.dumps(r)) 
    
    def post(self, method):
        logging.info(TRACE+'APICheckin:: post()')
        if method == 'new': 
            r = createCheckin(self)
        else: r = API404
        return self.response.out.write(simplejson.dumps(r)) 
        
class APIGame(webapp.RequestHandler):
    """Provides API access to Game data.  Responses are in JSON.
    """
    def get(self, mid, bgg_id):
        logging.info(TRACE+'APIGame:: get()')
        r = getGame(mid, bgg_id)
        return self.response.out.write(simplejson.dumps(r))
                
class APIUser(webapp.RequestHandler):
    """Provides API access to User data.  Responses are in JSON.
    """
    def get(self, fb_id):
        logging.info(TRACE+'APIUser:: get()')
        r = getUser(fb_id)
        return self.response.out.write(simplejson.dumps(r))         
               
class APIGameLog(webapp.RequestHandler):
    """Provides API access to GameLog data.  Responses are in JSON.
    """
    def get(self, checkin_id):
        logging.info(TRACE+'APIGameLog:: get()')
        r = getGameLog(checkin_id)
        return self.response.out.write(simplejson.dumps(r))         

    def post(self, method):
        logging.info(TRACE+'APIGameLog:: post()')
        if method == "new": 
            r = createGameLog(self)
        else: r = API404        
        return self.response.out.write(simplejson.dumps(r))

class APIUserBadges(webapp.RequestHandler):
    """Provides API access to a User's Badges.  Responses are in JSON.
    """
    def get(self, fb_id):
        logging.info(TRACE+'APIUserBadges:: get()')
        r = getUserBadges(fb_id)
        return self.response.out.write(simplejson.dumps(r))               

class APIError(webapp.RequestHandler):
    """Provides basic API error Response in JSON.
    """
    def get(self, foo):
        r = API404
        return self.response.out.write(simplejson.dumps(r)) 

    def post(self, foo):
        r = API404
        return self.response.out.write(simplejson.dumps(r)) 
               
######################## METHODS #############################################
##############################################################################
def getLatestCheckins(limit, time_since):
    """Returns lastest Checkins as a JSON Response.
    """
    logging.info(TRACE+'getLatestCheckins()')    
    q = models.Checkin.all()
    q.order("-created")
    q_checkins = q.fetch(limit)  
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    data = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin["created"] = str(c.created)
        checkin["id"] = str(c.key().id())
        data.append(checkin)
    r = API200
    r['result'] = data 
    return r

def getLatestUserCheckins(limit, time_since, fb_id):
    """Returns lastest Checkins for a given User as a JSON Response.
    """
    logging.info(TRACE+'getLatestUserCheckins()')
    user_key = db.Key.from_path('User', fb_id)   
    timestamp = datetime.datetime.fromtimestamp(time_since)
    q = models.Checkin.all()
    q.filter('created >', timestamp).filter('player =', user_key)
    q.order('-created', )    
    q_checkins = q.fetch(limit)  
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    data = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin["created"] = str(c.created)
        checkin["id"] = str(c.key().id())
        data.append(checkin)
    r = API200
    r['result'] = data 
    return r
 
def getGame(mid, bgg_id):
    """Returns JSON formated Game Response.
    """
    logging.info(TRACE+'getGame('+mid+','+bgg_id+')')    
    game = gamebase.getGame(mid, bgg_id)
    data = {"mid":game.mid, 
            "bgg_id":game.bgg_id, 
            "name":game.name,
            "description":game.description,
            "year_published":game.year_published,
            "playing_time":game.playing_time,
            "min_players":game.min_players,
            "max_players":game.max_players,
            "age":game.age,
            "publishers":game.publishers,
            "designers":game.designers,
            "expansions":game.expansions}
    r = API200
    r['result'] = data
    return r
    
def getUser(fb_id):
    """Returns JSON formated User Response.
    """
    logging.info(TRACE+'getUser('+fb_id+')')
    user = models.User.get_by_key_name(fb_id)    
    q_checkins = user.checkins.order('-created').fetch(10)
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin['created'] = str(c.created)
        checkin['id'] = str(c.key().id())
        checkins.append(checkin)
    data = {'name': user.name, 
            'fb_id': fb_id, 
            'fb_profile_url': user.fb_profile_url,
            'fb_location_id': user.fb_location_id,
            'fb_location_name': user.fb_location_name,
            'checkins': checkins}

    r = API200
    r['result'] = data 
    return r

def getGameLog(checkin_id):
    """Returns JSON formated GameLog Response.
    """
    logging.info(TRACE+'getGameLog('+checkin_id+')')
    q = models.Checkin.get_by_id(utils.strToInt(checkin_id)) 
    checkin = simplejson.loads(q.json)
    checkin['created'] = str(q.created)
    checkin['id'] = str(q.key().id())  
    data = {'checkin': checkin}
    r = API200
    r['result'] = data 
    return r 

def createGameLog(self):
    """Creates a new GameLog and returns the new GameLog as a JSON formatted
    Response.
    """
    checkin_id = self.request.get('checkin_id')
    game_log_json = checkinbase.createGameLog(self, checkin_id)
    data = {'gamelog': game_log_json}
    r = API200
    r['result'] = data 
    return r
    
def getUserBadges(fb_id):
    """Returns JSON formated User Badges Response.
    """
    logging.info(TRACE+'getUserBadges('+fb_id+')')
    user = models.User.get_by_key_name(fb_id)
    q_badges = db.get(user.badges)   
    badges = []
    for b in q_badges:
        badge = {'name': b.name,
                 'description': b.description,
                 'image_url': b.image_url,
                 'points': b.points,
                 'key': str(b.key())}
        badges.append(badge)     
    data = {'name': user.name, 
            'fb_id': fb_id, 
            'fb_profile_url': user.fb_profile_url,
            'fb_location_id': user.fb_location_id,
            'fb_location_name': user.fb_location_name,
            'badges': badges}
    r = API200
    r['result'] = data 
    return r         
 
def createCheckin(self):
    """Creates a new Checkin and returns any awarded Badges in a JSON
    formatted Response.
    """
    mid = self.request.get('mid')
    bgg_id = self.request.get('bgg_id')
    name = self.request.get('name')
    message = self.request.get('message')
    share = self.request.get('facebook')
    thumbnail = self.request.get('thumbnail')
    fb_id = self.request.get('fb_id')
    user_access_token = self.request.get('access_token')
    game_key = db.Key.from_path('Game', mid)
    user_key =db.Key.from_path('User', fb_id)
    game = models.Game.get(game_key)  
    user = models.User.get(user_key)  
    # Check user into game ...
    badges = checkinbase.createCheckin(user=user, game=game, 
                                       message=message, share=share)
    # Share checkin on Facebook if requested ...
    if share.upper() == 'TRUE':# Announce checkin on Facebook Wall
        logging.info(TRACE+'posting to Facebook '+user.access_token)
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
    
    data = {'badges': badges}       
    r = API200
    r['result'] = data 
    return r
                        
##############################################################################
##############################################################################
application = webapp.WSGIApplication([(r'/api/checkin/(.*)', APICheckin),
                                      (r'/api/game(/m/.*)/(.*)', APIGame),
                                      (r'/api/user/badges/(.*)', APIUserBadges),
                                      (r'/api/user/(.*)', APIUser),
                                      ('/api/gamelog/(.*)', APIGameLog),
                                      (r'/api/(.*)', APIError)
                                      ],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
