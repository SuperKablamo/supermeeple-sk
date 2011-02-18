# Datastore
import logging
from google.appengine.ext import db
from google.appengine.ext import blobstore

class User(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    fb_id = db.StringProperty(required=True)
    fb_profile_url = db.StringProperty(required=True)
    fb_location_id = db.StringProperty(required=False)
    fb_location_name = db.StringProperty(required=False)
    access_token = db.StringProperty(required=True)
    badges = db.ListProperty(db.Key, required=True, default=None)   
    last_checkin_time = db.DateTimeProperty(required=False)
    checkin_count = db.IntegerProperty(required=True, default=0)
    share_count = db.IntegerProperty(required=True, default=0)
    score_count = db.IntegerProperty(required=True, default=0)
    @property
    def gamelog_players(self):
        return GameLog.all().filter('players', self.key())    
            
class Game(db.Model): # mid is key_name
    name = db.StringProperty(required=True)
    bgg_id = db.StringProperty(required=False, default='0') # BoardGameGeek id
    mid = db.StringProperty(required=False) # Freebase mid
    asin = db.StringProperty(required=False) # ASIN number
    bgg_url = db.LinkProperty(required=False)
    bgg_img_url = db.LinkProperty(required=False)
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
    #  'message': message
    # }
    json = db.TextProperty(required=False)    

class Score(db.Model):
    game = db.ReferenceProperty(Game, required=True)
    player = db.ReferenceProperty(User, required=True)
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
    # {'players': 
    #     [{'name':name,'fb_id':fb_id,'point':points,'win':win},
    #      {'name':name,'fb_id':fb_id,'point':points,'win':win}],
    #  'note': note,
    #  'game': {'name':name,'mid':mid,'bgg_id':bgg_id,'bgg_thumbnail_url':url}
    # }
    json = db.TextProperty(required=False)    
  
class GameAward(db.Model): # award id is key_name
    json_dump = db.TextProperty(required=True)

class Badge(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty(required=True, default='description')
    points = db.IntegerProperty(required=True, default=0)   
    image = blobstore.BlobReferenceProperty(blobstore.BlobKey, required=False)
    image_url = db.LinkProperty(required=True, default="http://supermeeple.com.s3.amazonaws.com/yellow-1st.png")
    @property
    def checkin_badges(self):
        return Checkin.all().filter('badges', self.key())    
    @property
    def player_badges(self):
        return User.all().filter('badges', self.key())
    
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
