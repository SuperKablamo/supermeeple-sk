# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
from __future__ import with_statement

import gamebase
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
from google.appengine.api import files
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
    def get(self):
        logging.info('################### Admin:: get() ####################')
        badges = getBadges()
        game_seed_count = models.GameSeed.all().count(5000)
        processed_count = models.GameSeed.all().filter('processed = ', True).count(5000)
        game_count = models.Game.all().count(5000) 
        game_xml_count = models.GameXML.all().count(5000)
        image_upload_url = blobstore.create_upload_url('/upload/image')
        banner_upload_url = blobstore.create_upload_url('/upload/banner')
        checkin_counter = models.Game.all().filter('checkin_count >', 0).count()
        template_values = {
            'checkin_counter': checkin_counter,
            'game_seed_count': game_seed_count,
            'processed_count': processed_count,
            'game_count': game_count,
            'game_xml_count': game_xml_count,
            'badges': badges,
            'image_upload_url': image_upload_url,
            'banner_upload_url': banner_upload_url,            
            'facebook_app_id': FACEBOOK_APP_ID
        }  
        generate(self, 'base_admin.html', template_values)
        
    def post(self, method=None):
        logging.info('################## Admin:: post() ####################')
        logging.info('################## method = ' +method+' ##############')
        if method == "create-badges":
            result = deferred.defer(meeple_tasks.createBadges)
        if method == "add-badge":
            addBadge(self)            
        if method == "flush-seed-games":
            result = deferred.defer(meeple_tasks.flushSeedGames)          
        if method == "seed-games":
            result = deferred.defer(meeple_tasks.seedGames)
        if method == "build-games":
            buildGames(20)
        if method == "flush-cache":
            memcache.flush_all() 
        if method == "flush-games":
            pass
            # Very dangerous
            #flushGames()
        if method == "update-game":
            updateGame(self)  
        if method == "reset":
            reset(self)         
        self.redirect('/admin/')  

class GameEdit(webapp.RequestHandler):
    """Provides Admin access to editing Game data.
    """
    # Direct linking to Game Profile
    def get(self, mid=None, bgg_id=None):
        _trace = TRACE+'GameEdit:: '
        logging.info(_trace+'get(mid = '+mid+', bgg_id = '+bgg_id+')')
        game = gamebase.getGame(mid=mid, bgg_id=bgg_id)
        matches = gamebase.getBGGMatches(game.name, exact=False)
        template_values = {
            'game': game,
            'matches': matches
        }  
        generate(self, 'base_admin_game.html', template_values)
    
    # POST updated Game data.
    def post(self, mid=None, bgg_id=None):
        _trace = TRACE+'GameEdit:: '
        logging.info(_trace+'post(mid = '+mid+', bgg_id = '+bgg_id+')')        
        bgg_id_new = self.request.get('bgg-id')
        asin = self.request.get('asin')
        logging.info(_trace+'bgg_id_new = '+bgg_id_new)   
        logging.info(_trace+'asin = '+asin)                
        game = models.Game.get_by_key_name(mid)
        if asin != "None": game.asin = asin
        if bgg_id_new != "None": 
            game.bgg_id = bgg_id_new
            if bgg_id != bgg_id_new:
                gamebase.updateFreebaseBGGID(mid, bgg_id_new)
        game.put()
        memcache.delete(mid) # Clear old data from cache
        self.redirect('/admin/game'+mid+'/'+bgg_id_new)

class GameImageUpload(webapp.RequestHandler):
    """Provides Admin access to upload Game image.
    """    
    # POST updated Game image.
    def post(self, mid=None, bgg_id=None):
        _trace = TRACE+'GameImageUpload:: '
        logging.info(_trace+'post()')        
        logging.info(_trace+'mid = '+mid)                
        game = models.Game.get_by_key_name(mid)
        if game:
            # Store image    
            image_blob_key = storeImageFromBGG(game.bgg_image_url)
            image_url = None
            if image_blob_key is not None:
                image_url = images.get_serving_url(str(image_blob_key))    

            game.image = image_blob_key
            game.image_url = image_url
            game.put()
            memcache.delete(mid) # Clear old data from cache
        self.redirect('/admin/game'+mid+'/'+bgg_id)

class BGGDelete(webapp.RequestHandler):
    """Removes BGG ID from Freebase.
    """
    # POST Game and BGG to remove.
    def post(self, mid=None, bgg_id=None):
        logging.info('################# BGGDelete::post ####################')         
        game = models.Game.get_by_key_name(mid)
        game.bgg_id = "0"
        game.put()
        gamebase.updateFreebaseBGGID(mid, bgg_id, "delete")
        memcache.delete(mid) # Clear old data from cache
        self.redirect('/admin/game'+mid+'/'+game.bgg_id)

class UnmatchedGames(webapp.RequestHandler):
    """Provides Admin access to state of matched Games.
    """
    def get(self):
        logging.info('################# UnmatchedGames::get ################')
        q = models.Game.all()
        q.filter("bgg_id =", None)
        games = q.fetch(5000)
        template_values = {
            'games': games
        }  
        generate(self, 'base_admin_game_match.html', template_values)        
            
######################## METHODS #############################################
##############################################################################
def getBadges():
    '''Returns all Badge Entities in the Datastore.
    '''
    return models.Badge.all().fetch(500)

def addBadge(self):
    '''Creates a single Badge Entity in the Datastore.
    '''
    name = self.request.get('name')
    badge = models.Badge(key_name=name, name=name, description=name)
    db.put(badge)
    return badge
    
def buildGames(fetch_size=20):
    _trace = TRACE+'buildGames('+str(fetch_size)+') '
    logging.info(_trace)
    q = models.GameSeed.all().filter('processed = ', False).order('mid')
    game_seeds = q.fetch(fetch_size) 
    cursor = None
    count = 0
    task_number = 0
    game_seed_count = q.count(5000)
    logging.info(_trace+' game_seed_count = '+str(game_seed_count))
    while True:
        if cursor is None:
            logging.info(_trace+' cursor = None')
            game_seeds = q.fetch(fetch_size) 
        else:    
            logging.info(_trace+' cursor = '+str(cursor))
            game_seeds = q.with_cursor(cursor).fetch(fetch_size)
        cursor = q.cursor()
        keys = []
        for gs in game_seeds:
            keys.append(gs.key())
            count += 1
            logging.info(_trace+' count = '+str(count))
        task_number += 1
        logging.info(_trace+' defer() ')
        deferred.defer(meeple_tasks.processGameSeeds, 
                       keys, 
                       task_number, 
                       _queue='tortoise')     
        
        if count >= game_seed_count:
            return               

def flushGames():
    '''Deletes all Games.
    '''
    _trace = TRACE+'reset() '
    logging.info(_trace)    
    q = db.Query(models.Game, keys_only=True)
    keys = q.fetch(2000)
    db.delete(keys)
    return

def updateGame(self):
    return

def reset(self):
    '''Deletes all Checkins, Badges and Scores and resets counts.
    '''
    _trace = TRACE+'reset() '
    logging.info(_trace)
    
    # Reset counts on Games    
    logging.info(_trace+' reseting counts on Games.')
    games = models.Game.all().filter('checkin_count >', 0).fetch(5000)
    updated = []
    for g in games:
        g.checkin_count = 0
        updated.append(g)
    db.put(updated)

    # Clear earnings from Users
    logging.info(_trace+' clearing earnings from Users.')    
    users = models.User.all().fetch(1000)
    updated = []
    for u in users:
        u.badge_log = None
        u.badges = []
        u.checkin_count = 0
        u.score_count = 0
        u.share_count = 0
        updated.append(u)
    db.put(updated)
    
    # Delete GameLogs
    logging.info(_trace+' deleting all GameLogs.')        
    q = db.Query(models.GameLog, keys_only=True)   
    keys = q.fetch(2000)
    db.delete(keys)
         
    # Delete Scores
    logging.info(_trace+' deleting all Scores.')        
    q = db.Query(models.Score, keys_only=True)   
    keys = q.fetch(2000)
    db.delete(keys)
        
    # Delete Checkins
    logging.info(_trace+' deleting all Checkins.')        
    q = db.Query(models.Checkin, keys_only=True)   
    keys = q.fetch(2000)
    db.delete(keys)    
    
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
                                      (r'/admin/game-update(/m/.*)/(.*)', GameEdit),
                                      (r'/admin/game-image-upload(/m/.*)/(.*)', GameImageUpload),
                                      (r'/admin/bgg-delete(/m/.*)/(.*)', BGGDelete),
                                      ('/admin/', Admin),
                                      ('/admin/unmatched', UnmatchedGames),
                                      (r'/admin/(.*)', Admin)],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
