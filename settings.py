from google.appengine.ext import db

FACEBOOK_APP_ID = "149881721731503"
FACEBOOK_APP_SECRET = "8e79a7b1a2a58bc4824312094092c03e"
DEBUG = False
CHECKIN_FREQUENCY = 600 # Checkin frequency in seconds
UPDATE_FREQUENCY = 604800 # Game data update frequency in seconds
BGG_XML_URI = "http://www.boardgamegeek.com/xmlapi/boardgame/"
BGG_XML_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?exact=1&search="

BADGE_KEY_CHECKIN_A = db.Key.from_path('Badge', 'checkinA')
BADGE_KEY_CHECKIN_B = db.Key.from_path('Badge', 'checkinB')
BADGE_KEY_CHECKIN_C = db.Key.from_path('Badge', 'checkinC')
BADGE_KEY_CHECKIN_D = db.Key.from_path('Badge', 'checkinD')
BADGE_KEY_CHECKIN_E = db.Key.from_path('Badge', 'checkinE')
BADGE_KEY_CHECKIN_F = db.Key.from_path('Badge', 'checkinF')
BADGE_KEY_CHECKIN_G = db.Key.from_path('Badge', 'checkinG')