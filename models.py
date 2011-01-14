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
    #TODO: provide a common way to define places for Users of FB, Twitter . . .
    #current_location = db.ReferenceProperty(Location, required=False)   


    #class User(db.Model):
    #  created = db.DateTimeProperty(auto_now_add=True)
    #    updated = db.DateTimeProperty(auto_now=True)
    #    name = db.StringProperty(required=True)
    #    profile_url = db.StringProperty(required=True)
    #    access_token = db.StringProperty(required=True)
        #TODO: provide a common way to define places for Users of FB, Twitter . . .
        #current_location = db.ReferenceProperty(Location, required=False)
        # User needs to accomodate both FB, Twitter and Google.  Not sure if this is 
        # possible.
    

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
    totalRating = db.IntegerProperty(required=False, default=None)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(required=True, auto_now=True)

class GameXML(db.Model): # bgg_id is key_name
    xml = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class GameSession(db.Model):
    game = db.ReferenceProperty(Game)
    name = db.StringProperty(required=True)
    location = db.StringProperty(required=False)

class GameCheckin(db.Model):
    game = db.ReferenceProperty(Game)
    players = db.StringListPropery(required=True, default=None)
    user = db.ReferenceProperty(User)
    created = db.DateTimeProperty(required=True, auto_now=True)

class GameScore(db.Model):
    gameSession = db.ReferenceProperty(GameSession)
    points = db.IntegerProperty(required=True)       
    created = db.DateTimeProperty(required=True, auto_now=True)
    isWin = db.BooleanProperty(required=True, default=False)
    isVerified = db.BooleanProperty(required=True, default=False)
    
class GameRating(db.Model):
    game = db.ReferenceProperty(Game, required=True)  
    rating = db.IntegerProperty(required=True) 
    created = db.DateTimeProperty(required=True, auto_now=True)
  
class GameAward(db.Model): # award id is key_name
    json_dump = db.TextProperty(required=True)
    
