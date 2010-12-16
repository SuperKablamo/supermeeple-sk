# Datastore

from google.appengine.ext import db

# Location provides place context for Brags.
class Game(db.Model):
  freebaseID = db.StringProperty(required=True)
  freebaseGUID = db.StringProperty(required=True)
  bggURL = db.LinkProperty(required=False)
  totalRating = db.IntegerProperty(required=True)
  updated = db.DateTimeProperty(required=True, auto_now=True)

class Rating(db.Model):
  game = db.ReferenceProperty(Game, required=True)  
  rating = db.IntegerProperty(required=True) 
  created = db.DateTimeProperty(auto_now_add=True) 
   
   
    
