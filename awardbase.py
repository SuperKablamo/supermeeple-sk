# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# awardbase.py defines Methods for Badge resources.
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
import facebook
import freebase
import logging
import main
import models
import utils

from settings import *
from utils import strToInt

from django.utils import simplejson
from google.appengine.ext import db

############################# METHODS ########################################
##############################################################################
def awardCheckinBadges(user, game_key):
    """Returns any badges (as Keys) earned by a User.  Checks Checkins for 
    badge triggers.  If any triggers are met, the Badges are awarded.
    """
    _trace = TRACE+'awardCheckinBadges():: '
    keys = []
    ######## AWARD 1ST CHECKIN ###############################################
    q = models.Checkin.all()
    q.filter('game =', game_key)  
    any_checkin = q.get()
    if any_checkin is None: 
        logging.info(_trace+'awarding '+BADGE_CHKN_1ST['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_1ST['key']))   
        
    ######## AWARD CHECKIN LEVELS ############################################
    checkin_count = user.checkin_count
    if checkin_count == 2:
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_1['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_1['key']))   
    elif checkin_count == 8:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_2['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_2['key']))  
    elif checkin_count == 16:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_3['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_3['key'])) 
    elif checkin_count == 26:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_4['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_4['key']))
    elif checkin_count == 38:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_5['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_5['key']))
    elif checkin_count == 52:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_6['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_6['key']))
    elif checkin_count == 68:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_7['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_7['key']))
    elif checkin_count == 86:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_8['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_8['key']))  
    elif checkin_count == 106:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_9['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_9['key']))
    elif checkin_count == 128:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_10['key'])
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_10['key']))                                                       

    ######## AWARD SHARE LEVELS ##############################################
    share_count = user.share_count
    if share_count == 2:
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_1['key'])        
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_1['key']))   
    elif share_count == 8:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_2['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_2['key']))  
    elif share_count == 16:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_3['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_3['key'])) 
    elif share_count == 26:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_4['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_4['key']))
    elif share_count == 38:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_5['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_5['key']))
    elif share_count == 52:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_6['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_6['key']))
    elif share_count == 68:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_7['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_7['key']))
    elif share_count == 86:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_8['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_8['key']))  
    elif share_count == 106:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_9['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_9['key']))
    elif share_count == 128:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_10['key'])  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_10['key']))

    ######## AWARD BADGES ############################################
    # TODO: other badge awards go here . . .
    
    if not keys: 
        return None
    else: 
        return keys
    