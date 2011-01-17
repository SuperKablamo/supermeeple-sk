# Datastore

from google.appengine.ext import db

class User(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    fb_id = db.StringProperty(required=True)
    fb_profile_url = db.StringProperty(required=True)
    fb_location_id = db.StringProperty(required=False)
    fb_location_name = db.StringProperty(required=False)
    access_token = db.StringProperty(required=True)
    badges = db.StringListProperty(db.Key, required=True, default=None)    
    @property
    def checkins(self):
        return Checkin.all().filter('players', self.key())

class Game(db.Model): # mid is key_name
    name = db.StringProperty(required=True)
    bgg_id = db.StringProperty(required=False) # BoardGameGeek id
    mid = db.StringProperty(required=False) # Freebase mid
    bgg_url = db.LinkProperty(required=False)
    bgg_img_url = db.LinkProperty(required=False)
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
    totalRating = db.IntegerProperty(required=False, default=0)
    checkin_count = db.IntegerProperty(required=True, default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(required=True, auto_now=True)

class GameXML(db.Model): # bgg_id is key_name
    xml = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class Checkin(db.Model):
    game = db.ReferenceProperty(Game, required=True, collection_name="checkins")
    players = db.ListProperty(db.Key, required=True, default=None)
    badges = db.ListProperty(db.Key, required=True, default=None)
    winner = db.ReferenceProperty(User, required=False, collection_name="wins")
    fb_location_id = db.StringProperty(required=False)
    fb_location_name = db.StringProperty(required=False)
    created = db.DateTimeProperty(required=True, auto_now=True)
    json = db.TextProperty(required=False)
  
class GameAward(db.Model): # award id is key_name
    json_dump = db.TextProperty(required=True)

class Badge(db.Model):
    name = db.StringProperty(required=True)
    img_url = db.LinkProperty(required=True, default='/foo.jpg')
    points = db.IntegerProperty(required=True, default=0)    
    @property
    def checkin_badges(self):
        return Checkin.all().filter('badges', self.key())    
    @property
    def player_badges(self):
        return User.all().filter('badges', self.key())

class Score(db.Model):
    checkin = db.ReferenceProperty(Checkin, required=True)
    game = db.ReferenceProperty(Game, required=True)
    player = db.ReferenceProperty(User, required=True)
    points = db.IntegerProperty(required=True, default=0)
    flags = db.IntegerProperty(required=True, default=0)
    
class GameRating(db.Model):
    game = db.ReferenceProperty(Game, required=True)  
    rating = db.IntegerProperty(required=True) 
    created = db.DateTimeProperty(required=True, auto_now=True)
    
