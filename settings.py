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
BADGE_CHECKIN_COUNT_A = 'Gamer'
BADGE_CHECKIN_COUNT_B = 'Board Game Geek'
BADGE_CHECKIN_COUNT_C = 'Board Game Fanatic'
BADGE_GAME_CHECKIN_FIRST = 'Pioneer Meeple'

