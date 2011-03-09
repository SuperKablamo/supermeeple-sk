#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

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
    """Returns any badges earned by a User.  Checks Checkins for badge
    triggers.  If any triggers are met, the Badges are awarded/saved.
    """
    keys = []
    ######## AWARD 1ST CHECKIN ###############################################
    q = models.Checkin.all()
    q.filter('game =', game_key)  
    any_checkin = q.get()
    if any_checkin is None: 
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_1ST))   
        
    ######## AWARD CHECKIN LEVELS ############################################
    checkin_count = user.checkin_count
    if checkin_count == 2:
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_1))   
    elif checkin_count == 8:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_2))  
    elif checkin_count == 16:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_3)) 
    elif checkin_count == 26:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_4))
    elif checkin_count == 38:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_5))
    elif checkin_count == 52:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_6))
    elif checkin_count == 68:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_7))
    elif checkin_count == 86:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_8))  
    elif checkin_count == 106:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_9))
    elif checkin_count == 128:    
        keys.append(db.Key.from_path('Badge', BADGE_CHKN_LVL_10))                                                       

    ######## AWARD CHARE LEVELS ##############################################
    share_count = user.share_count
    if share_count == 2:
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_1))   
    elif share_count == 8:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_2))  
    elif share_count == 16:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_3)) 
    elif share_count == 26:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_4))
    elif share_count == 38:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_5))
    elif share_count == 52:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_6))
    elif share_count == 68:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_7))
    elif share_count == 86:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_8))  
    elif share_count == 106:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_9))
    elif share_count == 128:    
        keys.append(db.Key.from_path('Badge', BADGE_SHARE_LVL_10))

    ######## AWARD BADGES ############################################
    # TODO: other badge awards go here . . .
    
    if not keys: return None
    else:
        user.badges.extend(keys)
        user.put() 
        return db.Model.get(keys)