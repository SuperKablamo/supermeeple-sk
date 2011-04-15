# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# GAE IMPORTS ####################################
##############################################################################
import logging

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.ext import blobstore

############################# CUSTOM PROPERTIES ##############################
##############################################################################   
class JSONProperty(db.TextProperty):
    def validate(self, value):
        return value
 
    def get_value_for_datastore(self, model_instance):
        result = super(JSONProperty, self).get_value_for_datastore(model_instance)
        result = simplejson.dumps(result)
        return db.Text(result)
	 
    def make_value_from_datastore(self, value):
        try:
            value = simplejson.loads(str(value))
        except:
            pass

        return super(JSONProperty, self).make_value_from_datastore(value)

############################# MODELS  ########################################
##############################################################################
class User(db.Model): # fb_id is key_name
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    fb_id = db.StringProperty(required=True)
    fb_profile_url = db.LinkProperty(required=False)
    fb_location_id = db.StringProperty(required=False)
    fb_location_name = db.StringProperty(required=False)
    access_token = db.StringProperty(required=True, default='0')
    last_checkin_time = db.DateTimeProperty(required=False)
    checkin_count = db.IntegerProperty(required=True, default=0)
    share_count = db.IntegerProperty(required=True, default=0)
    score_count = db.IntegerProperty(required=True, default=0)
    badges = db.ListProperty(db.Key, required=True, default=None)
    badge_log = JSONProperty(required=True, default=None)
    welcomed = db.BooleanProperty(required=True, default=False)
    alerted = db.BooleanProperty(required=True, default=False)
    @property
    def gamelog_players(self):
        return GameLog.all().filter('players', self.key())    
            
class Game(db.Model): # mid is key_name
    name = db.StringProperty(required=True)
    bgg_id = db.StringProperty(required=False, default='0') # BoardGameGeek id
    mid = db.StringProperty(required=False) # Freebase mid
    asin = db.StringProperty(required=False) # ASIN number
    image = blobstore.BlobReferenceProperty(blobstore.BlobKey, required=False)
    image_url = db.LinkProperty(required=False)
    bgg_url = db.LinkProperty(required=False)
    bgg_image_url = db.LinkProperty(required=False)
    bgg_thumbnail_url = db.LinkProperty(required=False)
    description = db.TextProperty(required=False)
    year_published = db.IntegerProperty(required=False)
    min_players = db.IntegerProperty(required=False)
    max_players = db.IntegerProperty(required=False)
    playing_time = db.IntegerProperty(required=False)
    age = db.IntegerProperty(required=False)
    publishers = db.StringListProperty(required=True, default=None) 
    designers = db.StringListProperty(required=True, default=None) 
    artists = db.StringListProperty(required=True, default=None) 
    expansions = db.StringListProperty(required=True, default=None) 
    mechanics = db.StringListProperty(required=True, default=None) 
    awards = db.StringListProperty(required=True, default=None) 
    categories = db.StringListProperty(required=True, default=None)  
    subdomains = db.StringListProperty(required=True, default=None)     
    checkin_count = db.IntegerProperty(required=True, default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(required=True, auto_now=True)

class GameXML(db.Model): # bgg_id is key_name
    # BGG Game XML example: http://www.boardgamegeek.com/xmlapi/boardgame/13
    xml = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class Checkin(db.Model):
    game = db.ReferenceProperty(Game, required=True, collection_name='checkins')
    player = db.ReferenceProperty(User, required=True, collection_name='checkins')
    badges = db.ListProperty(db.Key, required=True, default=None)
    winner = db.ReferenceProperty(User, required=False, collection_name='wins')
    fb_location_id = db.StringProperty(required=False)
    fb_location_name = db.StringProperty(required=False)
    created = db.DateTimeProperty(required=True, auto_now=True)
    message = db.StringProperty(required=True, default="message")
    
    # {'player': 
    #     {'name':name,'fb_id':fb_id},
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url}],
    #  'message': message,
    #  'gamelog':
    #     {'scores':
    #       [{'name':name,'fb_id':fb_id,'point':points,'win':win},
    #        {'name':name,'fb_id':fb_id,'point':points,'win':win}],
    #      'note': note}    
    json = db.TextProperty(required=False)    

class Score(db.Model):
    author = db.ReferenceProperty(User, required=True, collection_name='scored')
    game = db.ReferenceProperty(Game, required=True, collection_name='scores')
    player = db.ReferenceProperty(User, required=True, collection_name='scores')
    gamelog_id = db.IntegerProperty(required=True)
    points = db.IntegerProperty(required=True, default=0)
    flags = db.IntegerProperty(required=True, default=0)
    win = db.BooleanProperty(required=True, default=False)
    created = db.DateTimeProperty(required=True, auto_now=True)
    @property
    def gamelog_scores(self):
        return GameLog.all().filter('scores', self.key())    

class GameLog(db.Model):
    checkin = db.ReferenceProperty(Checkin, required=True)
    game = db.ReferenceProperty(Game, required=True)
    players = db.ListProperty(db.Key, required=True, default=None)
    scores = db.ListProperty(db.Key, required=True, default=None)
    note = db.StringProperty(required=False)
  
class GameAward(db.Model): # award id is key_name
    json_dump = db.TextProperty(required=True)

class Badge(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty(required=True, default='description')
    points = db.IntegerProperty(required=True, default=0)   
    image = blobstore.BlobReferenceProperty(blobstore.BlobKey, required=False)
    banner = blobstore.BlobReferenceProperty(blobstore.BlobKey, required=False)
    image_url = db.LinkProperty(required=True, default="http://supermeeple.com.s3.amazonaws.com/checkin1_100x100.png")
    banner_url = db.LinkProperty(required=True, default="http://supermeeple.com.s3.amazonaws.com/firstcheck_banner.png")    
    @property
    def checkin_badges(self):
        return Checkin.all().filter('badges', self.key())    
    @property
    def player_badges(self):
        return User.all().filter('badges', self.key())

class BadgeAward(db.Model):
    badge = db.ReferenceProperty(Badge, required=True, collection_name='badge_awards')
    user = db.ReferenceProperty(User, required=True, collection_name='badge_awards')
    games = db.ListProperty(db.Key, required=True, default=None)  
    created = db.DateTimeProperty(required=True, auto_now=True)
        
class GameRating(db.Model):
    game = db.ReferenceProperty(Game, required=True)  
    rating = db.IntegerProperty(required=True) 
    created = db.DateTimeProperty(required=True, auto_now=True)
    
class GameSeed(db.Model): # mid is key_name
    bgg_id = db.StringProperty(required=False, default=None) # BoardGameGeek id
    mid = db.StringProperty(required=True) # Freebase mid
    name = db.StringProperty(required=True)
    processed = db.BooleanProperty(required=True, default=False)
    created = db.DateTimeProperty(required=True, auto_now=True)

class Config(db.Model):
    game_seed_cursor = db.StringProperty(required=False)   
    unmatched_games = db.ListProperty(db.Key, required=True, default=None)
