# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

import freebase

## APPSPOT.COM - UNCOMMENT FOR PRODUCTION ####################################
#FACEBOOK_APP_ID = "149881721731503"
#FACEBOOK_APP_SECRET = "95d5f3afab330cdc970e120e519c36d6"
#SITE="SuperMeeple"
##############################################################################

## LOCALHOST:8080 - UNCOMMENT FOR LOCAL TESTING ##############################
FACEBOOK_APP_ID = "174331539272451"
FACEBOOK_APP_SECRET = "173988eedb97c654f3cfe2d60ce6129d"
SITE="localhosttest-sk"
##############################################################################

TOKEN = 'access_token'

CONFIG_KEY_NAME = "v1"
DEBUG = False
TRACE = '##TRACE##  '

CHECKIN_FREQUENCY = 10 # Checkin frequency in seconds
#CHECKIN_FREQUENCY = 300 # Checkin frequency in seconds
UPDATE_FREQUENCY = 604800 # Game data update frequency in seconds
BGG_XML_URI = "http://www.boardgamegeek.com/xmlapi/boardgame/"
BGG_XML_EXACT_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?exact=1&search="
BGG_XML_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?search="
BGG_NAMESPACE = "/user/pak21/boardgamegeek/boardgame"

## FREEBASE LIVE #############################################################
FREEBASE_USER = "supermeeple"
FREEBASE_PSWD = "Super52556!"
FREEBASE = freebase

## FREEBASE SANDBOX ##########################################################
#FREEBASE_USER = "wmerydith"
#FREEBASE_PSWD = "free1945"
#FREEBASE = freebase.sandbox

################### WE DO NEED SOME STINKIN' BADGES ##########################
BADGE_CHKN_1ST = 'Pioneer'
BADGE_ORIGINS_2011 = 'Origins 2011'
BADGE_PAXW_2011 = 'PAX West 2011'
BADGE_GENCON_2011 = 'GenCon 2011'
BADGE_CHKN_LVL_1 = 'Level 1 Game Geek'
BADGE_CHKN_LVL_2 = 'Level 2 Game Geek'
BADGE_CHKN_LVL_3 = 'Level 3 Game Geek' 
BADGE_CHKN_LVL_4 = 'Level 4 Game Geek'
BADGE_CHKN_LVL_5 = 'Level 5 Game Geek'
BADGE_CHKN_LVL_6 = 'Level 6 Game Geek'
BADGE_CHKN_LVL_7 = 'Level 7 Game Geek'
BADGE_CHKN_LVL_8 = 'Level 8 Game Geek'
BADGE_CHKN_LVL_9 = 'Level 9 Game Geek'
BADGE_CHKN_LVL_10 = 'Level 10 Game Geek'
BADGE_SHARE_LVL_1 = 'Level 1 Social Gamer'
BADGE_SHARE_LVL_2 = 'Level 2 Social Gamer'
BADGE_SHARE_LVL_3 = 'Level 3 Social Gamer' 
BADGE_SHARE_LVL_4 = 'Level 4 Social Gamer'
BADGE_SHARE_LVL_5 = 'Level 5 Social Gamer'
BADGE_SHARE_LVL_6 = 'Level 6 Social Gamer'
BADGE_SHARE_LVL_7 = 'Level 7 Social Gamer'
BADGE_SHARE_LVL_8 = 'Level 8 Social Gamer'
BADGE_SHARE_LVL_9 = 'Level 9 Social Gamer'
BADGE_SHARE_LVL_10 = 'Level 10 Social Gamer'

BADGES = [BADGE_CHKN_1ST, BADGE_ORIGINS_2011, BADGE_PAXW_2011,
          BADGE_GENCON_2011, BADGE_CHKN_LVL_1, BADGE_CHKN_LVL_2, 
          BADGE_CHKN_LVL_3, BADGE_CHKN_LVL_4, BADGE_CHKN_LVL_5,
          BADGE_CHKN_LVL_6, BADGE_CHKN_LVL_7, BADGE_CHKN_LVL_8,
          BADGE_CHKN_LVL_9, BADGE_CHKN_LVL_10, BADGE_SHARE_LVL_1,
          BADGE_SHARE_LVL_2, BADGE_SHARE_LVL_3, BADGE_SHARE_LVL_4,
          BADGE_SHARE_LVL_5, BADGE_SHARE_LVL_6, BADGE_SHARE_LVL_7,
          BADGE_SHARE_LVL_8, BADGE_SHARE_LVL_9, BADGE_SHARE_LVL_10]