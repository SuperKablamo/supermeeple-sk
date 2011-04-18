# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# api.py defines Handlers and Methods for providing API access to 
# SuperMeeple.com.
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
        logging.info(_trace+'awarding '+BADGE_CHKN_1ST)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_1ST))   
        
    ######## AWARD CHECKIN LEVELS ############################################
    checkin_count = user.checkin_count
    if checkin_count == 2:
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_1)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_1))   
    elif checkin_count == 8:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_2)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_2))  
    elif checkin_count == 16:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_3)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_3)) 
    elif checkin_count == 26:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_4)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_4))
    elif checkin_count == 38:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_5)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_5))
    elif checkin_count == 52:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_6)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_6))
    elif checkin_count == 68:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_7)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_7))
    elif checkin_count == 86:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_8)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_8))  
    elif checkin_count == 106:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_9)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_9))
    elif checkin_count == 128:    
        logging.info(_trace+'awarding '+BADGE_CHKN_LVL_10)
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_10))                                                       

    ######## AWARD SHARE LEVELS ##############################################
    share_count = user.share_count
    if share_count == 2:
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_1)        
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_1))   
    elif share_count == 8:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_2)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_2))  
    elif share_count == 16:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_3)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_3)) 
    elif share_count == 26:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_4)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_4))
    elif share_count == 38:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_5)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_5))
    elif share_count == 52:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_6)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_6))
    elif share_count == 68:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_7)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_7))
    elif share_count == 86:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_8)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_8))  
    elif share_count == 106:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_9)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_9))
    elif share_count == 128:    
        logging.info(_trace+'awarding '+BADGE_SHARE_LVL_10)  
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_10))

    ######## AWARD BADGES ############################################
    # TODO: other badge awards go here . . .
    
    if not keys: 
        return None
    else: 
        return keys