# Datastore

from google.appengine.ext import db

class User(db.Model):
    name = db.StringProperty(required=True)
    rating = db.IntegerProperty(required=True)

class Game(db.Model):
    freebaseID = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    bggURL = db.LinkProperty(required=False)
    totalRating = db.IntegerProperty(required=False)
    updated = db.DateTimeProperty(required=True, auto_now=True)

class GameData(db.Model):
    data = db.StringProperty(required=True)

class GameSession(db.Model):
    game = db.ReferenceProperty(Game)
    location = db.StringProperty(required=True)

class GameCheckin(db.Model):
    gameSession = db.ReferenceProperty(GameSession)
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
  
  
   
   
    
