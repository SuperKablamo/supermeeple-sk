#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import meeple_tasks
import models
import utils
from settings import *
from utils import strToInt
from utils import buildDataList
from utils import findPrimaryName

import os
import cgi
import freebase
import logging
import facebook
import datetime
import re
import urllib2

from urlparse import urlparse
from xml.etree import ElementTree 
from django.utils import simplejson
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
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

class Admin(webapp.RequestHandler):
    """Provides Admin access to data-entry and initialization tasks.
    """
    def get(self, pswd=None):
        logging.info('################### Admin:: get() ####################')
        logging.info('################### pswd =' +pswd+ ' #################')        
        if pswd == "backyardchicken":
            badges = getBadges()
            game_seed_count = models.GameSeed.all().count(5000)
            processed_count = models.GameSeed.all().filter('processed = ', True).count(5000)
            game_count = models.Game.all().count(5000) 
            game_xml_count = models.GameXML.all().count(5000)
            image_upload_url = blobstore.create_upload_url('/upload/image')
            template_values = {
                'game_seed_count': game_seed_count,
                'processed_count': processed_count,
                'game_count': game_count,
                'game_xml_count': game_xml_count,
                'badges': badges,
                'image_upload_url': image_upload_url,
                'facebook_app_id': FACEBOOK_APP_ID
            }  
            generate(self, 'base_admin.html', template_values)
        else: self.redirect(500)  
        
    def post(self, method=None):
        logging.info('################### Admin:: post() ###################')
        logging.info('################### method =' +method+' ##############')
        if method == "create-badges":
            createBadges()
        if method == "flush-seed-games":
            result = deferred.defer(meeple_tasks.flushSeedGames)          
        if method == "seed-games":
            result = deferred.defer(meeple_tasks.seedGames)
        if method == "build-games":
            buildGames(20)
        if method == "flush-cache":
            memcache.flush_all()    
        self.redirect('/admin/backyardchicken')  

class GameEdit(webapp.RequestHandler):
    """Provides Admin access to editing Game data.
    """
    # Direct linking to Game Profile
    def get(self, mid=None, bgg_id=None):
        logging.info('################# GameEdit::get ######################')
        game = getGame(self=self, mid=mid, bgg_id=bgg_id)
        template_values = {
            'game': game,
            'current_user': user,
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        self.generate(self, 'base_admin_game.html', template_values)
        
######################## METHODS #############################################
##############################################################################

def createBadges():
    updated = []    
    for b in BADGES:
        badge = models.Badge.get_by_key_name(b)
        if badge is None:
            logging.info('############# Creating Badge '+b+ '###############')
            badge = models.Badge(key_name=b, name=b, description=b)
            updated.append(badge)
   
    db.put(updated)
    return None                      

def getBadges():
    """Returns all Badge Entities in the Datastore"""
    return models.Badge.all().fetch(500)
    
def buildGames(fetch_size=20):
    logging.info('#################### buildGames() ########################')
    q = models.GameSeed.all().filter('processed = ', False).order('mid')
    game_seeds = q.fetch(fetch_size) 
    cursor = None
    count = 0
    task_number = 0
    game_seed_count = q.count(5000)
    logging.info('####### game_seed_count = '+str(game_seed_count)+' #######')
    while True:
        if cursor is None:
            logging.info('###### buildGames():: cursor = None  #############')
            game_seeds = q.fetch(fetch_size) 
        else:    
            logging.info('###### buildGames():: cursor = '+str(cursor)+ ' ##')
            game_seeds = q.with_cursor(cursor).fetch(fetch_size)
        cursor = q.cursor()
        keys = []
        for gs in game_seeds:
            keys.append(gs.key())
            count += 1
            logging.info('####### buildGames() :: count = '+str(count)+' ###')
        task_number += 1
        logging.info('################ buildGames() :: defer() #############')
        deferred.defer(meeple_tasks.processGameSeeds, 
                       keys, 
                       task_number, 
                       _queue="tortoise")     
        
        if count >= game_seed_count:
            return               

def generate(self, template_name, template_values):
    template.register_template_library('templatefilters')
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, 
                        os.path.join('templates', template_name))

    self.response.out.write(template.render(path, 
                                            template_values, 
                                            debug=DEBUG))

##############################################################################
##############################################################################
application = webapp.WSGIApplication([(r'/admin/game(/m/.*)/(.*)', GameEdit),
                                      (r'/admin/(.*)', Admin),],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()