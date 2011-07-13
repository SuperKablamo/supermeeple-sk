# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================
import freebase

import os

DEV = os.environ['SERVER_SOFTWARE'].startswith('Development')

# Settings for development
if DEV:
    FACEBOOK_APP_ID = "174331539272451"
    FACEBOOK_APP_SECRET = "173988eedb97c654f3cfe2d60ce6129d"
    SITE="localhosttest-sk" 
    FREEBASE_USER = "wmerydith"
    FREEBASE_PSWD = "free1945"
    FREEBASE = freebase.sandbox    
    CHECKIN_FREQUENCY = 10 # Checkin frequency in seconds

# Settngs for production    
else:
    FACEBOOK_APP_ID = "149881721731503"
    FACEBOOK_APP_SECRET = "95d5f3afab330cdc970e120e519c36d6"
    SITE="SuperMeeple"
    FREEBASE_USER = "supermeeple"
    FREEBASE_PSWD = "Super52556!"
    FREEBASE = freebase    
    CHECKIN_FREQUENCY = 300 # Checkin frequency in seconds
    
TOKEN = 'access_token'
CONFIG_KEY_NAME = "v1"
DEBUG = False
TRACE = '##TRACE##  '
UPDATE_FREQUENCY = 604800 # Game data update frequency in seconds
BGG_XML_URI = "http://www.boardgamegeek.com/xmlapi/boardgame/"
BGG_XML_EXACT_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?exact=1&search="
BGG_XML_SEARCH = "http://www.boardgamegeek.com/xmlapi/search?search="
BGG_NAMESPACE = "/user/pak21/boardgamegeek/boardgame"
 
SPIEL_ID = "/m/0gxr36p"
MEEPLES_ID = "/en/meeples_choice_award"        