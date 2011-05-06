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

##############################################################################
### !!! NOTE - THESE ARE KEY NAMES, CHANGING THEM WILL BREAK THE SITE !!! ####
##############################################################################
BADGE_CHKN_1ST = {'key':'BADGE_CHKN_1ST','cat':'Pioneer', 'lvl':'1', 'description':'This is what you get for being first!'}
BADGE_ORIGINS_2011 = {'key':'BADGE_ORIGINS_2011','cat':'Origins', 'lvl':'2011', 'description':'Your friends back home are jealous.'}
BADGE_PAXW_2011 = {'key':'BADGE_PAXW_2011','cat':'PAX West', 'lvl':'2011', 'description':'Gaming with the Penny Arcade team.'}
BADGE_GENCON_2011 = {'key':'BADGE_GENCON_2011','cat':'GenCon', 'lvl':'2011', 'description':'Roll one for Gary Gygax.'}
BADGE_CHKN_LVL_1 = {'key':'BADGE_CHKN_LVL_1','cat':'Game Geek', 'lvl':'1', 'description':'You\'re a level 1 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_2 = {'key':'BADGE_CHKN_LVL_2','cat':'Game Geek', 'lvl':'2', 'description':'You\'re a level 2 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_3 = {'key':'BADGE_CHKN_LVL_3','cat':'Game Geek', 'lvl':'3', 'description':'You\'re a level 3 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_4 = {'key':'BADGE_CHKN_LVL_4','cat':'Game Geek', 'lvl':'4', 'description':'You\'re a level 4 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_5 = {'key':'BADGE_CHKN_LVL_5','cat':'Game Geek', 'lvl':'5', 'description':'You\'re a level 5 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_6 = {'key':'BADGE_CHKN_LVL_6','cat':'Game Geek', 'lvl':'6', 'description':'You\'re a level 6 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_7 = {'key':'BADGE_CHKN_LVL_7','cat':'Game Geek', 'lvl':'7', 'description':'You\'re a level 7 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_8 = {'key':'BADGE_CHKN_LVL_8','cat':'Game Geek', 'lvl':'8', 'description':'You\'re a level 8 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_9 = {'key':'BADGE_CHKN_LVL_9','cat':'Game Geek', 'lvl':'9', 'description':'You\'re a level 9 Game Geek.  Level up with more checkins.'}
BADGE_CHKN_LVL_10 = {'key':'BADGE_CHKN_LVL_10','cat':'Game Geek', 'lvl':'10', 'description':'You\'re a level 10 Game Geek.  Level up with more checkins.'}
BADGE_SHARE_LVL_1 = {'key':'BADGE_SHARE_LVL_1','cat':'Social Gamer', 'lvl':'1', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_2 = {'key':'BADGE_SHARE_LVL_2','cat':'Social Gamer', 'lvl':'2', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_3 = {'key':'BADGE_SHARE_LVL_3','cat':'Social Gamer', 'lvl':'3', 'description':'You like to brag about your love for games.  Share more and level up.'} 
BADGE_SHARE_LVL_4 = {'key':'BADGE_SHARE_LVL_4','cat':'Social Gamer', 'lvl':'4', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_5 = {'key':'BADGE_SHARE_LVL_5','cat':'Social Gamer', 'lvl':'5', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_6 = {'key':'BADGE_SHARE_LVL_6','cat':'Social Gamer', 'lvl':'6', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_7 = {'key':'BADGE_SHARE_LVL_7','cat':'Social Gamer', 'lvl':'7', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_8 = {'key':'BADGE_SHARE_LVL_8','cat':'Social Gamer', 'lvl':'8', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_9 = {'key':'BADGE_SHARE_LVL_9','cat':'Social Gamer', 'lvl':'9', 'description':'You like to brag about your love for games.  Share more and level up.'}
BADGE_SHARE_LVL_10 = {'key':'BADGE_SHARE_LVL_10','cat':'Social Gamer', 'lvl':'10', 'description':'You like to brag about your love for games.  Share more and level up.'}

BADGES = [BADGE_CHKN_1ST, BADGE_ORIGINS_2011, BADGE_PAXW_2011,
          BADGE_GENCON_2011, BADGE_CHKN_LVL_1, BADGE_CHKN_LVL_2, 
          BADGE_CHKN_LVL_3, BADGE_CHKN_LVL_4, BADGE_CHKN_LVL_5,
          BADGE_CHKN_LVL_6, BADGE_CHKN_LVL_7, BADGE_CHKN_LVL_8,
          BADGE_CHKN_LVL_9, BADGE_CHKN_LVL_10, BADGE_SHARE_LVL_1,
          BADGE_SHARE_LVL_2, BADGE_SHARE_LVL_3, BADGE_SHARE_LVL_4,
          BADGE_SHARE_LVL_5, BADGE_SHARE_LVL_6, BADGE_SHARE_LVL_7,
          BADGE_SHARE_LVL_8, BADGE_SHARE_LVL_9, BADGE_SHARE_LVL_10]
          
BADGE_CATS = ['Pioneer', 'Origins', 'PAX West', 'GenCon', 'Game Geek', 
              'Social Gamer']
                        
##############################################################################          