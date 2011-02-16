import freebase

## APPSPOT.COM - UNCOMMENT FOR PRODUCTION ####################################
#FACEBOOK_APP_ID = "149881721731503"
#FACEBOOK_APP_SECRET = "8e79a7b1a2a58bc4824312094092c03e"
#SITE="SuperMeeple"
##############################################################################

## LOCALHOST:8080 - UNCOMMENT FOR LOCAL TESTING ##############################
FACEBOOK_APP_ID = "174331539272451"
FACEBOOK_APP_SECRET = "f4f8e3762a2abbe62dee8bf44a4967a4"
SITE="localhosttest-sk"
##############################################################################

CONFIG_KEY_NAME = "v1"
DEBUG = False
#CHECKIN_FREQUENCY = 50 # Checkin frequency in seconds
CHECKIN_FREQUENCY = 300 # Checkin frequency in seconds
UPDATE_FREQUENCY = 604800 # Game data update frequency in seconds
BGG_XML_URI = "http://www.boardgamegeek.com/xmlapi/boardgame/"
BGG_XML_EXACT_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?exact=1&search="
BGG_XML_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?search="
BGG_NAMESPACE = "/user/pak21/boardgamegeek/boardgame"

## FREEBASE LIVE #############################################################
#FREEBASE_USER = "supermeeple"
#FREEBASE_PSWD = "Super52556!"
#FREEBASE = freebase

## FREEBASE SANDBOX ##########################################################
FREEBASE_USER = "wmerydith"
FREEBASE_PSWD = "free1945"
FREEBASE = freebase.sandbox

################### WE DO NEED SOME STINKIN' BADGES ##########################
BADGE_CHKN_1ST = 'Pioneer'
BADGE_CHKN_LVL_1 = 'Board Game Geek lvl 1'
BADGE_CHKN_LVL_2 = 'Board Game Geek lvl 2'
BADGE_CHKN_LVL_3 = 'Board Game Geek lvl 3' 
BADGE_CHKN_LVL_4 = 'Board Game Geek lvl 4'
BADGE_CHKN_LVL_5 = 'Board Game Geek lvl 5'
BADGE_CHKN_LVL_6 = 'Board Game Geek lvl 6'
BADGE_CHKN_LVL_7 = 'Board Game Geek lvl 7'
BADGE_CHKN_LVL_8 = 'Board Game Geek lvl 8'
BADGE_CHKN_LVL_9 = 'Board Game Geek lvl 9'
BADGE_CHKN_LVL_10 = 'Board Game Geek lvl 10'
BADGE_SHARE_LVL_1 = 'Board Game Evangelist lvl 1'
BADGE_SHARE_LVL_2 = 'Board Game Evangelist lvl 2'
BADGE_SHARE_LVL_3 = 'Board Game Evangelist lvl 3' 
BADGE_SHARE_LVL_4 = 'Board Game Evangelist lvl 4'
BADGE_SHARE_LVL_5 = 'Board Game Evangelist lvl 5'
BADGE_SHARE_LVL_6 = 'Board Game Evangelist lvl 6'
BADGE_SHARE_LVL_7 = 'Board Game Evangelist lvl 7'
BADGE_SHARE_LVL_8 = 'Board Game Evangelist lvl 8'
BADGE_SHARE_LVL_9 = 'Board Game Evangelist lvl 9'
BADGE_SHARE_LVL_10 = 'Board Game Evangelist lvl 10'

BADGES = [BADGE_CHKN_1ST, BADGE_CHKN_LVL_1, BADGE_CHKN_LVL_2, 
          BADGE_CHKN_LVL_3, BADGE_CHKN_LVL_4, BADGE_CHKN_LVL_5,
          BADGE_CHKN_LVL_6, BADGE_CHKN_LVL_7, BADGE_CHKN_LVL_8,
          BADGE_CHKN_LVL_9, BADGE_CHKN_LVL_10, BADGE_SHARE_LVL_1,
          BADGE_SHARE_LVL_2, BADGE_SHARE_LVL_3, BADGE_SHARE_LVL_4,
          BADGE_SHARE_LVL_5, BADGE_SHARE_LVL_6, BADGE_SHARE_LVL_7,
          BADGE_SHARE_LVL_8, BADGE_SHARE_LVL_9, BADGE_SHARE_LVL_10]