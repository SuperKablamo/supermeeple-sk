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
from google.appengine.ext.db import polymodel
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
    share_list = db.StringListProperty(required=True, default=None)
    badges = db.ListProperty(db.Key, required=True, default=None)
    welcomed = db.BooleanProperty(required=True, default=False)
    alerted = db.BooleanProperty(required=True, default=False)
    active = db.BooleanProperty(required=True, default=False)
    @property
    def gamelog_players(self):
        return GameLog.all().filter('players', self.key())    
            
class Game(db.Model): # mid is key_name
    name = db.StringProperty(required=True)
    asin = db.StringProperty(required=False) # ASIN number
    image = blobstore.BlobReferenceProperty(blobstore.BlobKey, required=False)
    image_url = db.LinkProperty(required=False)
    youtube_url = db.LinkProperty(required=False)
    checkin_count = db.IntegerProperty(required=True, default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(required=True, auto_now=True)

class GameLog(polymodel.PolyModel):
    game = db.ReferenceProperty(Game, required=True, collection_name='checkins')
    player = db.ReferenceProperty(User, required=True, collection_name='checkins')
    badges = db.ListProperty(db.Key, required=True, default=None)
    created = db.DateTimeProperty(auto_now_add=True)

class Checkin(GameLog):
    location = db.GeoPtProperty(required=False)
    place = db.StringProperty(required=False)
    message = db.StringProperty(required=True, default="message")
    
    # {'game':
    #     {'name':name,'image_url':image_url},
    #  'player': 
    #     {'name':name,'fb_id':fb_id},
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url,
    #         'banner_image_url':banner_image_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url,
    #         'banner_image_url':banner_image_url}],
    #  'place':place,
    #  'message': message
    # }    
    json = db.TextProperty(required=False)    

class Badge(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty(required=True, default='description')
    points = db.IntegerProperty(required=True, default=0)   
    image = blobstore.BlobReferenceProperty(blobstore.BlobKey, required=False)
    banner_image = blobstore.BlobReferenceProperty(blobstore.BlobKey, required=False)
    level = db.IntegerProperty(required=True, default=1)
    category = db.StringProperty(required=True)
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
    
class GameAward(db.Model): # award id is key_name
    json = db.TextProperty(required=True)
