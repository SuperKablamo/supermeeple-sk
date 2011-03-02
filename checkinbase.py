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

from google.appengine.ext import db

############################# METHODS ########################################
##############################################################################

def shareGameLog(share, user, checkin_json):
    if share.upper() == 'TRUE':# Announce checkin on Facebook Wall
        logging.info('#### posting to Facebook '+user.access_token+'####')
        # Build Game data ...
        game = models.Game.get_by_key_name(checkin_json['game']['mid'])
        thumbnail = game.bgg_thumbnail_url
        if thumbnail is None:
            thumbnail = 'http://api.freebase.com/api/trans/image_thumb'+game.mid+'?maxwidth=80&maxheight=100'
        gamelog = checkin_json['gamelog']
        description = utils.smart_truncate(game.description, length=300)    
        
        # Build String of Player Scores ...
        # TODO: It would be great if Facebook players could be tagged.
        players = []
        for s in gamelog['scores']:
            player = s['name']+' - '+s['points']+' points.'
            players.append(player)
        s = ' '.join(players)
        message = s + ' ' + gamelog['note']
        
        # Build GraphAPI Request ...
        url = 'http://www.supermeeple.com/user/' + user.fb_id
        caption = "SuperMeeple: Board Game Database, Tools and Apps"
        attachment = {}
        attachment['caption'] = caption
        attachment['name'] = 'Scored a game of ' + game.name 
        attachment['link'] = url #url
        attachment['description'] = description   
        attachment['picture'] = thumbnail
        action_link = 'http://www.supermeeple.com/game'+str(game.mid)+'/'+str(game.bgg_id)
        action_name = "Check In!"
        actions = {"name": action_name, "link": action_link}
        attachment['actions'] = actions     
        results = facebook.GraphAPI(
           user.access_token).put_wall_post(message, attachment)    
    return

def getGameHighScores(game, count=10):
    """Returns high Scores for a Game.
    """
    logging.info('##################### getGameHighScores ##################')    
    ref_scores = game.scores.order('-points').fetch(count)
    deref_scores = utils.prefetch_refprops(ref_scores, models.Score.player)
    return deref_scores   

def getScoresFromFriends(profile_user, count=10):
    """Returns Scores for a User that were added by their friends.
    """
    logging.info('##################### getScoresFromFriends ###############')    
    query = profile_user.scores.filter('author !=', profile_user)
    ref_scores = query.fetch(count)
    deref_scores = utils.prefetch_refprops(ref_scores,
                                           models.Score.author,
                                           models.Score.game)
    return deref_scores    