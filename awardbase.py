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

############################# CONSTANTS ######################################
##############################################################################

#!!! NOTE - THESE ARE KEY NAMES, CHANGING THEM WILL BREAK THE SITE !!! ####
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
    