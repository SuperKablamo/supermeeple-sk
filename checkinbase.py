# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
import awardbase
import datetime
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
from google.appengine.ext import deferred

############################# METHODS ########################################
##############################################################################
def createCheckin(user, game, message, share=False):
    _trace = TRACE + 'createCheckin():: '
    logging.info(_trace)
    # Create initial json data:
    # {'player': 
    #     {'name':name,'fb_id':fb_id},
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}],
    #  'message': message,
    #  'game':
    #     {'name':name,'mid':mid,'bgg_id':bgg_id,'bgg_image_url':bgg_image_url,'img_url':img_url}
    # }
    player = {'name' : user.name, 'fb_id': user.fb_id}
    user.checkin_count += 1
    game.checkin_count += 1
    badge_keys = awardbase.awardCheckinBadges(user, game.key()) 
    badge_entities = None
    if badge_keys is not None:
        logging.info(_trace+'getting badge entities for badge_keys ...')
        badge_entities = db.Model.get(badge_keys)     
    badges=[]
    updates = [] # List for batch put()
    game_data = {'name': game.name, 
                 'mid': game.mid, 
                 'bgg_id': game.bgg_id, 
                 'bgg_thumbnail_url': game.bgg_thumbnail_url,
                 'image_url':game.image_url}
                 
    if badge_entities is not None:
        for b in badge_entities:
            logging.info(_trace+'badge.name = ' +str(b.name))
            logging.info(_trace+'badge.image_url= ' +str(b.image_url))
            badge = {'name': b.name, 
                     'image_url': b.image_url,
                     'banner_url': b.banner_url,
                     'key_name': b.key().name()}
            badges.append(badge)  
            user.badges.append(b.key())
            if user.badge_log is None:
                user.badge_log = {}
            if b.key().name() in user.badge_log:
                user.badge_log[b.key().name()]['games'].append(game_data) 
            else:
                data = {'badge': badge, 'games': [game_data]}
                user.badge_log[b.key().name()] = data
        
    json_dict = {'player': player, 
                 'badges': badges, 
                 'message': message, 
                 'game': game_data}
    json = simplejson.dumps(json_dict)  
    checkin = models.Checkin(player=user, 
                             game=game.key(), 
                             message=message,
                             json=db.Text(json))    
    
    user.last_checkin_time = datetime.datetime.now()
    updates.append(user)
    updates.append(game)
    updates.append(checkin)
    db.put(updates)
    json_dict['id'] = checkin.key().id()
    json_dict['created'] = str(checkin.created)
    return json_dict

def isCheckedIn(user):
    """Returns True if the User is checked into a Game with the check in grace
    period.   
    """
    time = datetime.datetime.now() - datetime.timedelta(0, CHECKIN_FREQUENCY)
    try:
        last_time = user.last_checkin_time
    except AttributeError:
        return False    
    if last_time is None:
        return False
    elif last_time > time:
        return True

def getUserCheckins(user, count=10):
    """Returns Checkins for a User.
    """
    # Data format:
    # [{'id':id,    
    #   'player': 
    #       {'name': name, 'fb_id': fb_id},
    #   'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}],
    #   'created': '3 minutes ago',
    #   'game': 
    #     {'name': name,'mid':mid,'bgg_id':bgg_id,'bgg_image_url':bgg_url,'image_url':image_url},
    #   'message': 'message    
    #   'gamelog':
    #     {'note':note, 
    #      [{'winner':boolean, 'points':int, 'name':player, 'fb_id':fb_id},
    #       {'winner':boolean, 'points':int, 'name':player, 'fb_id':fb_id}]
    #     } 
    #  }]    
    q_checkins = user.checkins.order('-created').fetch(count)
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin['created'] = c.created
        checkin['id'] = str(c.key().id())
        checkins.append(checkin)
        logging.info('############# checkin ='+str(checkin)+' ##############')
    return checkins

def getGameCheckins(game, count=10):
    """Returns Checkins for a Game.
    """
    logging.info('##################### getGameCheckins ####################')    
    # Data format:
    # [{'id':id,     
    #   'player': 
    #       {'name': name, 'fb_id': fb_id},
    #   'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}],
    #   'created': '3 minutes ago'
    #   'message': 'message    
    #  }]
    ref_checkins = game.checkins.order('-created').fetch(count)
    checkins = [] 
    for c in ref_checkins:
        checkin = simplejson.loads(c.json)
        checkin['created'] = c.created
        checkin['id'] = str(c.key().id())
        checkins.append(checkin)
        logging.info('############### checkin ='+str(checkin)+' ############')
    return checkins   

def getLatestCheckins(count=10):
    """Returns lastest Checkins.
    """
    logging.info('##################### getLatestCheckins ##################')    
    # Data format:
    # [{'id':id,     
    #   'player':
    #       {'name': name, 'fb_id': fb_id},
    #  'badges': 
    #       [{'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}, 
    #        {'name':name,'key_name':key_name,'image_url':image_url,'banner_url':banner_url}],
    #   'created': '3 minutes ago',
    #   'game': 
    #     {'name': name, 'mid': mid, "bgg_id": bgg_id, "bgg_image_url": url, 'image_url':image_url},
    #    'message': 'message
    #  }]
    q = models.Checkin.all()
    q.order('-created')
    q_checkins = q.fetch(count)  
    deref_checkins = utils.prefetch_refprops(q_checkins, 
                                             models.Checkin.game)    
    checkins = []
    for c in deref_checkins:
        checkin = simplejson.loads(c.json)
        checkin['created'] = c.created
        checkin['id'] = str(c.key().id())
        checkins.append(checkin)
        logging.info('############# checkin ='+str(checkin)+' ##############')
    return checkins

def createGameLog(self, checkin_id):
    """Creates new GameLog and Returns JSON Response of Checkin, Scores,
    Badges and Game.
    """
    logging.info('############## createGameLog('+checkin_id+') #############')
    game_log = models.GameLog.get_by_key_name(checkin_id)  
    if game_log: return # game_log already exists!
    checkin = models.Checkin.get_by_id(strToInt(checkin_id))
    user = models.User.get_by_key_name(self.request.get('fb_id1'))    
    # Read and organize data ...
    note = self.request.get('note')
    mid = self.request.get('mid')  
    logging.info('############# note = '+note+' ##########')
    logging.info('############# mid = '+mid+' ##########') 
    game_key = db.Key.from_path('Game', mid)         
    scores = [] 
    player_keys = []
    entities = []
    count = 1
    while (count < 9):
        player_name = self.request.get('name'+str(count))
        if player_name:
            player_id = self.request.get('fb_id'+str(count)) 
            points = self.request.get('score'+str(count))
            win = self.request.get('win'+str(count))
            if win == "True": win = True
            else: win = False
            score = {"name":player_name,
                     "fb_id":player_id,
                     "points":points,
                     "winner":win}
            logging.info('#### score '+str(count)+' '+str(score)+' ###')
            scores.append(score)                    
            if player_id: # Only Facebook Players ...
                player_key = db.Key.from_path('User', player_id)
                player = models.User.get(player_key)
                # If the player has never logged on, create them
                if player is None:
                    player = main.createLiteUser(player_name, player_id)
                    entities.append(player)
                player_keys.append(player_key)
                # Create Score ...
                entity = models.Score(game=game_key,
                                      player=player_key,
                                      gamelog_id=strToInt(checkin_id),
                                      points=strToInt(points),
                                      win=win, 
                                      author=user)
                entities.append(entity)
        count += 1
        
    # Update Checkin with JSON string of Scores ...    
    game_log_json = {'scores':scores, 'note':note}    
    checkin_json_dict = simplejson.loads(checkin.json)
    checkin_json_dict['gamelog'] = game_log_json
    checkin_json_txt = simplejson.dumps(checkin_json_dict)
    checkin.json = db.Text(checkin_json_txt)
    entities.append(checkin)
    
    # Create a new GameLog ...
    game_log = models.GameLog(key_name=checkin_id,
                              game=game_key,
                              checkin=checkin,
                              note=note,
                              players=player_keys)
    entities.append(game_log)
    
    # Update User's score count ...
    user.score_count += 1
    entities.append(user)
            
    # Save all entities
    db.put(entities)
  
    # Share gamelog on Facebook if requested ...
    share = self.request.get('facebook')
    if share.upper() == 'TRUE':
        deferred.defer(shareGameLog, user, simplejson.loads(checkin.json))

    return game_log_json

def shareCheckin(user, game):
    _trace = TRACE+'shareCheckin():: '
    logging.info(_trace+'posting to Facebook '+user.access_token)
    attachment = {}
    description = utils.smart_truncate(game.description, length=300)
    url = 'http://www.supermeeple.com' + game.mid + '/' + game.bgg_id
    thumbnail = 'http://api.freebase.com/api/trans/image_thumb'+game.mid+'?maxwidth=80&maxheight=100'
    if game.image_url is not None:
        thumbnail = game.image_url+'=s100'    
    caption = "SuperMeeple: Board Game Database, Tools and Apps"
    attachment['caption'] = caption
    attachment['name'] = game.name
    attachment['link'] = url #url
    attachment['description'] = description   
    attachment['picture'] = thumbnail
    action_link = 'http://www.supermeeple.com'+str(mid)+'/'+str(bgg_id)
    action_name = "Check In!"
    actions = {"name": action_name, "link": action_link}
    attachment['actions'] = actions     
    results = facebook.GraphAPI(
       user.access_token).put_wall_post(message, attachment)    
    return   

def shareGameLog(user, checkin_json):
    logging.info('#### posting to Facebook '+user.access_token+'####')
    # Build Game data ...
    game = models.Game.get_by_key_name(checkin_json['game']['mid'])
    thumbnail = 'http://api.freebase.com/api/trans/image_thumb'+game.mid+'?maxwidth=80&maxheight=100'
    if game.image_url is not None:
        thumbnail = game.image_url+'=s100'
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

def getBadgeLog(profile_user):
    """Returns a Template friendly badge_log.
    """    
    _trace = TRACE + 'getBadgeLog():: '
    logging.info(_trace)    
    keys = profile_user.badge_log.keys()
    badge_log = []
    for k in keys:
        log_entry = profile_user.badge_log[k]
        data = {'badge': log_entry['badge'], 'games': log_entry['games']}
        badge_log.append(data)
    
    return badge_log

