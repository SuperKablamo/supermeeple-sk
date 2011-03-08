#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#
# api.py defines Handlers and Methods for providing API access to 
# SuperMeeple.com.
#

############################# IMPORTS ########################################
############################################################################## 
import checkinbase
import gamebase
import models
import utils

import os
import logging
import urllib2

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

############################# REQUEST HANDLERS ############################### 
##############################################################################
class APICheckin(webapp.RequestHandler):
    """Provides API access to Checkin data.  Responses are in JSON.
    """
    def get(self, method):
        logging.info('################### APICheckin:: get() ###############')
        if method == "latest": r = getLatestCheckins()
        else: r = {"status": "200 OK", "code": "/api/status/error"}
        return self.response.out.write(simplejson.dumps(r)) 
        
class APIGame(webapp.RequestHandler):
    """Provides API access to Game data.  Responses are in JSON.
    """
    def get(self, mid, bgg_id):
        logging.info('################### APIGame:: get() ##################')
        r = getGame(mid, bgg_id)
        return self.response.out.write(simplejson.dumps(r))
                
class APIUser(webapp.RequestHandler):
    """Provides API access to User data.  Responses are in JSON.
    """
    def get(self, fb_id):
        logging.info('################### APIUser:: get() ##################')
        r = getUser(fb_id)
        return self.response.out.write(simplejson.dumps(r))         
               
class APIGameLog(webapp.RequestHandler):
    """Provides API access to GameLog data.  Responses are in JSON.
    """
    def get(self, checkin_id):
        logging.info('################### APIGameLog:: get() ###############')
        r = getGameLog(checkin_id)
        return self.response.out.write(simplejson.dumps(r))         

class APIUserBadges(webapp.RequestHandler):
    """Provides API access to a User's Badges.  Responses are in JSON.
    """
    def get(self, fb_id):
        logging.info('################# APIUserBadges:: get() ##############')
        r = getUserBadges(fb_id)
        return self.response.out.write(simplejson.dumps(r))               
               
######################## METHODS #############################################
##############################################################################
def getLatestCheckins(count=10):
    """Returns lastest Checkins as a JSON Response.
    """
    logging.info('##################### getLatestCheckins ##################')    
    q = models.Checkin.all()
    q.order("-created")
    q_checkins = q.fetch(count)  
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin["created"] = str(c.created)
        checkins.append(checkin)
    r = {'status': '200 OK', 'code': '/api/status/ok', 'result': r} 
    return r
 
def getGame(mid, bgg_id):
    """Returns JSON formated Game Response.
    """
    logging.info('################## getGame('+mid+','+bgg_id+') ###########')    
    game = gamebase.getGame(mid, bgg_id)
    r = {"mid":game.mid, 
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
    r = {'status': '200 OK', 'code': '/api/status/ok', 'result': r} 
    return r
    
def getUser(fb_id):
    """Returns JSON formated User Response.
    """
    logging.info('#################### getUser('+fb_id+') ##################')
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
    r = {'name': user.name, 
         'fb_id': fb_id, 
         'fb_profile_url': user.fb_profile_url,
         'fb_location_id': user.fb_location_id,
         'fb_location_name': user.fb_location_name,
         'checkins': checkins}

    r = {'status': '200 OK', 'code': '/api/status/ok', 'result': r} 
    return r

def getGameLog(checkin_id):
    """Returns JSON formated GameLog Response.
    """
    logging.info('############### getGameLog('+checkin_id+') ###############')
    q = models.Checkin.get_by_id(utils.strToInt(checkin_id)) 
    checkin = simplejson.loads(q.json)
    checkin['created'] = str(q.created)
    checkin['id'] = str(q.key().id())  
    r = {'checkin': checkin}
    r = {'status': '200 OK', 'code': '/api/status/ok', 'result': r} 
    return r 

def getUserBadges(fb_id):
    """Returns JSON formated User Badges Response.
    """
    logging.info('############### getUserBadges('+fb_id+') #################')
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
    r = {'name': user.name, 
         'fb_id': fb_id, 
         'fb_profile_url': user.fb_profile_url,
         'fb_location_id': user.fb_location_id,
         'fb_location_name': user.fb_location_name,
         'badges': badges}
    r = {'status': '200 OK', 'code': '/api/status/ok', 'result': r} 
    return r         
                    
##############################################################################
##############################################################################
application = webapp.WSGIApplication([(r'/api/checkin/(.*)', APICheckin),
                                      (r'/api/game(/m/.*)/(.*)', APIGame),
                                      (r'/api/user/badges/(.*)', APIUserBadges),
                                      (r'/api/user/(.*)', APIUser),
                                      ('/api/gamelog/(.*)', APIGameLog)
                                      ],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
