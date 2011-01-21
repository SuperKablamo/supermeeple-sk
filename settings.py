from google.appengine.ext import db

## LOCALHOST:8080 - UNCOMMENT FOR LOCAL TESTING ##############################
FACEBOOK_APP_ID = "174331539272451"
FACEBOOK_APP_SECRET = "f4f8e3762a2abbe62dee8bf44a4967a4"
SITE="localhosttest-sk"
##############################################################################
#FACEBOOK_APP_ID = "149881721731503"
#FACEBOOK_APP_SECRET = "8e79a7b1a2a58bc4824312094092c03e"
#SITE="SuperMeeple"
DEBUG = False
CHECKIN_FREQUENCY = 50 # Checkin frequency in seconds
#CHECKIN_FREQUENCY = 300 # Checkin frequency in seconds
UPDATE_FREQUENCY = 604800 # Game data update frequency in seconds
BGG_XML_URI = "http://www.boardgamegeek.com/xmlapi/boardgame/"
BGG_XML_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?exact=1&search="


################### WE DO NEED SOME STINKIN' BADGES ##########################
BADGE_NAME_CHECKIN_COUNT_A = 'count_A'
BADGE_NAME_CHECKIN_COUNT_B = 'count_B'
BADGE_NAME_CHECKIN_COUNT_C = 'count_C'
BADGE_NAME_CHECKIN_COUNT_D = 'count_D'
BADGE_NAME_CHECKIN_COUNT_E = 'count_E'
BADGE_NAME_CHECKIN_COUNT_F = 'count_F'
BADGE_NAME_CHECKIN_COUNT_G = 'count_G'
BADGE_NAME_GAME_CHECKIN_FIRST = 'Pioneer Meeple'

BADGE_KEY_CHECKIN_COUNT_A = db.Key.from_path('Badge', BADGE_NAME_CHECKIN_COUNT_A)
BADGE_KEY_CHECKIN_COUNT_B = db.Key.from_path('Badge', BADGE_NAME_CHECKIN_COUNT_B)
BADGE_KEY_CHECKIN_COUNT_C = db.Key.from_path('Badge', BADGE_NAME_CHECKIN_COUNT_C)
BADGE_KEY_CHECKIN_COUNT_D = db.Key.from_path('Badge', BADGE_NAME_CHECKIN_COUNT_D)
BADGE_KEY_CHECKIN_COUNT_E = db.Key.from_path('Badge', BADGE_NAME_CHECKIN_COUNT_E)
BADGE_KEY_CHECKIN_COUNT_F = db.Key.from_path('Badge', BADGE_NAME_CHECKIN_COUNT_F)
BADGE_KEY_CHECKIN_COUNT_G = db.Key.from_path('Badge', BADGE_NAME_CHECKIN_COUNT_G)
BADGE_KEY_GAME_CHECKIN_FIRST = db.Key.from_path('Badge', BADGE_NAME_GAME_CHECKIN_FIRST)

BADGE_IMG_CHECKIN_COUNT_A = '/static/images/meeple-yellow.png'
BADGE_IMG_CHECKIN_COUNT_B = '/static/images/meeple-green.png'
BADGE_IMG_CHECKIN_COUNT_C = '/static/images/meeple-blue.png'
BADGE_IMG_CHECKIN_COUNT_D = '/static/images/meeple-yellow.png'
BADGE_IMG_CHECKIN_COUNT_E = '/static/images/meeple-yellow.png'
BADGE_IMG_CHECKIN_COUNT_F = '/static/images/meeple-yellow.png'
BADGE_IMG_CHECKIN_COUNT_G = '/static/images/meeple-yellow.png'
BADGE_IMG_GAME_CHECKIN_FIRST = '/static/images/meeple-red.png'

