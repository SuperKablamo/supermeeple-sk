# Datastore

from google.appengine.ext import db

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    # TODO: provide a common way to define places for Users of FB, Twitter . . .
    #current_location = db.ReferenceProperty(Location, required=False)

class Game(db.Model):
    name = db.StringProperty(required=True)
    bggURL = db.LinkProperty(required=False)
    bggID = db.IntegerProperty(required=False)
    totalRating = db.IntegerProperty(required=False)
    updated = db.DateTimeProperty(required=True, auto_now=True)

class GameData(db.Model):
    data = db.StringProperty(required=True)

class GameSession(db.Model):
    game = db.ReferenceProperty(Game)
    name = db.StringProperty(required=True)
    location = db.StringProperty(required=False)

class GameCheckin(db.Model):
    game = db.ReferenceProperty(Game)
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
  
  
   
   
    
