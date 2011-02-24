#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import gamebase
import models
import utils

import os
import logging
import urllib2

from django.utils import simplejson
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
        game = {"name": c.game.name, 
                "mid": str(c.game.mid), 
                "bgg_id": c.game.bgg_id, 
                "bgg_img_url": c.game.bgg_thumbnail_url}
        checkin["game"] = game
        checkins.append(checkin)
        logging.info('############# checkin ='+str(checkin)+' ##############')
    r = {"status": "200 OK", "code": "/api/status/ok", "result": checkins}
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
    r = {"status": "200 OK", "code": "/api/status/ok", "result": r}
    return r
                
##############################################################################
##############################################################################
application = webapp.WSGIApplication([(r'/api/checkin/(.*)', APICheckin),
                                      (r'/api/game(/m/.*)/(.*)', APIGame)#,
                                      #(r'/api/user/(.*)', APIUser),
                                      #('/api/score/(.*)', APIScore)
                                      ],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
