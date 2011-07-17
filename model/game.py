# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
from __future__ import with_statement

import freebase
import logging
import main
import models
import urllib2

from settings import *
from utils import strToInt
from utils import buildDataList
from utils import findPrimaryName
from xml.etree import ElementTree 

from google.appengine.api import files
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors

############################# METHODS ########################################
##############################################################################

def getGame(mid):
    '''Returns a Game.  Looks for one in memcache, if not then creates one
    using Freebase API.
    '''
    _trace = TRACE+'getGame('+mid+'):: '
    logging.info(_trace)
    
    if mid is None: return None
    game_cache = memcache.get(mid)
    
    if game_cache is None: # If this Game is not cached, build a new cache
        game = models.Game.get_by_key_name(mid)
        
        if game is None: # Game has never been stored, so build and store it.
            game = buildFBGame(mid)
                        
        else: # Game has been stored, get it, update data.
            game = updateFBGame(mid, game)
            success = memcache.set(key=mid, 
                                   value=game, 
                                   time=432000) # expiration 5 days
        
        game_cache = game        
    
    return game_cache

def buildFBGame(mid):
    '''Builds a Game from the Freebase API.
    '''
    fb_game = getFBGame(mid)
    game_data = parseFBJSON(fb_game)
    game_blurb = getFBGameBlurb(mid, 2000)
    
    if game_blurb is not None:
        game_data['description'] = db.Text(game_blurb.decode("utf-8"))  
    else:
        game_data['description'] = None     
         
    game = models.Game(key_name=mid,
                       freebase_data=game_data)
                       
    game.put()
    success = memcache.set(key=mid, 
                           value=game, 
                           time=432000) # expiration 5 days 
    
    return game

def updateFBGame(mid, game):
    '''Updates a Game using the Freebase API.
    '''
    fb_game = getFBGame(mid)
    game_data = parseFBJSON(fb_game)
    game_blurb = getFBGameBlurb(mid, 2000)
    
    if game_blurb is not None:
        game_data['description'] = db.Text(game_blurb.decode("utf-8"))  
    else:
        game_data['description'] = None     
         
    game.freebase_data = game_data
    game.put()
    success = memcache.set(key=mid, 
                           value=game, 
                           time=432000) # expiration 5 days 
    
    return game

def getFBGame(mid):
    '''Returns a JSON result for Freebase Game data.    
    '''
    _trace = TRACE+'getFBGame('+mid+'):: '
    logging.info(_trace)    
    query = {
      "mid":           mid,
      "type":          "/games/game",
      "name":          None,
      "introduced":    None,
      "/games/game/number_of_players": {
        "high_value": None,
        "low_value":  None,
        "optional": True
      },      
      "playing_time_minutes": None,
      "minimum_age_years": None,
      "publisher":     [],
      "designer":      [],
      "expansions":    [], 
      "genre":         [],
      "game_subjects": [],     
      "key" : {
        "namespace" : "/user/pak21/boardgamegeek/boardgame",
        "value" : None,
        "optional": True
      }
    }       
    return FREEBASE.mqlread(query, extended=True)

def parseFBJSON(json):
    '''Returns a dictionary of game data retrieved from Freebase.
    '''
    _trace = TRACE+'parseFBJSON('+str(json)+')'
    logging.info(_trace)
    fb_data = {'name': json.name}
    
    if json.introduced is not None: 
        fb_data['year_published'] = strToInt(json.introduced)  
    else: fb_data['year_published'] = None      
    
    if json["/games/game/number_of_players"] is not None:
        fb_data['min_players'] = strToInt(json[
                                "/games/game/number_of_players"].high_value)
        
        fb_data['max_players'] = strToInt(json[
                                "/games/game/number_of_players"].low_value)
    
    else: 
        fb_data['min_players'] = None
        fb_data['max_players'] = None
    
    if json.playing_time_minutes is not None:
        fb_data['playing_time'] = strToInt(json.playing_time_minutes)
    else: fb_data['playing_time'] = None
    
    if json.minimum_age_years is not None:
        fb_data['age'] = strToInt(json.minimum_age_years)
    else: fb_data['age'] = None   
    
    if json.publisher is not None:
        fb_data['publishers'] = json.publisher
    else: fb_data['publishers'] = None
    
    if json.designer is not None:
        fb_data['designers'] = json.designer
    else: fb_data['designers'] = None
    
    if json.expansions is not None:
        fb_data['expansions'] = json.expansions  
    else: fb_data['expansions'] = None    
    
    if json.genre is not None:
        fb_data['genres'] = json.genre  
    else: fb_data['genres'] = None    

    if json.game_subjects is not None:
        fb_data['subjects'] = json.game_subjects  
    else: fb_data['subjects'] = None    
    
    if json.key is not None:
        fb_data['bgg_id'] = json.key.value
    else: fb_data['bgg_id'] = None
        
    return fb_data

def getFBGameBlurb(mid, length=800):
    '''Returns a description of the Game.  Freebase stores descriptions in a 
    datastore separate from the rest of the data, and can only be retrieved 
    using the Trans service.
    '''
    _trace = TRACE+'getFBGameBlurb('+mid+', '+str(length)+')'
    logging.info(_trace)    
    try:
        blurb = FREEBASE.blurb(mid, break_paragraphs=True, maxlength=length)
    except Exception:
        # The Freebase module raises a MetawebError if a blurb is not found
        return None
    return blurb

def parseBGGXML(bgg_id):
    '''Returns a dictionary of game data retrieved from BGGs XML API.
    '''
    _trace = TRACE+'parseBGGXML('+bgg_id+'):: '
    logging.info(_trace)
    
    bgg_game_url = BGG_XML_URI + bgg_id
    result = urllib2.urlopen(bgg_game_url).read()
    try:
        xml = ElementTree.fromstring(result)
    except Exception:
        logging.info(TRACE+'parseBGGXML() error parsing BGG')
        return None  
    decoded_result = result.decode("utf-8")
    xml_text = db.Text(decoded_result)
    bgg_data = {'name': findPrimaryName(xml),
                'description': xml.findtext(".//description"),
                'year_published': strToInt(xml.findtext(".//yearpublished")),
                'min_players': strToInt(xml.findtext(".//minplayers")),
                'max_players': strToInt(xml.findtext(".//maxplayers")),
                'playing_time': strToInt(xml.findtext(".//playingtime")),
                'age': strToInt(xml.findtext(".//age")),
                'publishers': 
                    buildDataList(xml.findall(".//boardgamepublisher")),
                'artists': buildDataList(xml.findall(".//boardgameartist")),
                'designers': 
                    buildDataList(xml.findall(".//boardgamedesigner")),  
                'expansions': 
                    buildDataList(xml.findall(".//boardgameexpansion")),
                'categories': 
                    buildDataList(xml.findall(".//boardgamecategory")),
                'mechanics': 
                    buildDataList(xml.findall(".//boardgamemechanic")),
                'subdomains': 
                    buildDataList(xml.findall(".//boardgamesubdomain")),
                'image_url': xml.findtext(".//image"),
                'thumbnail_url':xml.findtext(".//thumbnail"),
                'xml_text': xml_text}
    
    return bgg_data
    
def storeImageFromBGG(bgg_image_url):
    '''Returns a blob_key for an image fetched from BGG and stored to the 
    BlobStore.
    '''
    _trace = TRACE+'storeImageFromBGG():: '
    logging.info(_trace)
    image_blob_key = None
    if bgg_image_url is not None:
        image_name = bgg_image_url.split('/')[-1]        
        file_name = files.blobstore.create(mime_type='image/jpeg', 
                                           _blobinfo_uploaded_filename=image_name)
    
        # Sometimes the image from BGG is too large for GAE ...
        try: 
            image = urllib2.urlopen(bgg_image_url)
            with files.open(file_name, 'a') as f:
                f.write(image.read())
                # Get a smaller version ...        
        except apiproxy_errors.RequestTooLargeError:
            bgg_md_image_url = bgg_image_url.replace('.jpg', '_md.jpg')
            image = urllib2.urlopen(bgg_md_image_url)
            with files.open(file_name, 'a') as f:
                f.write(image.read())
        finally:
            files.finalize(file_name)   
            image_blob_key = files.blobstore.get_blob_key(file_name)
    else:
        return None
            
    return image_blob_key

def getBGGIDFromBGG(game_name):
    """Returns the Board Game Geek Game ID from Board Game Geek.    
    """
    logging.info(TRACE+'getBGGIDFromBGG():: finding bgg_id')
    logging.info(TRACE+'getBGGIDFromBGG():: game_name = ' + game_name)   
    try:
        game_url = BGG_XML_SEARCH + urllib2.quote(game_name.encode('utf8'))
    except KeyError: # Most likely foreign characters in game_name
        return None    
    logging.info(TRACE+'getBGGIDFromBGG():: game_url = ' + game_url) 
    try:
        result = urllib2.urlopen(game_url).read()
    except Exception:
        return None
    xml = ElementTree.fromstring(result)
    try:
        bgg_id = xml.find("./boardgame").attrib['objectid']
    except AttributeError:
        logging.info(TRACE+'getBGGIDFromBGG():: NO MATCH') 
        return None    
    logging.info(TRACE+'getBGGIDFromBGG():: MATCH FOUND!')         
    logging.info(TRACE+'getBGGIDFromBGG():: bgg_id = ' + str(bgg_id)) 
    return bgg_id

def getBGGMatches(game_name, exact=True): 
    """Returns Board Game Geek Game IDs from Board Game Geek given a Game
    name.  If exact=True, then the search is for a single exact match.  If
    exact=False, then the search returns all possible matches.   
    """
    logging.info(TRACE+'getBGGMatches():: finding bgg_id')
    logging.info(TRACE+'getBGGMatches():: game_name = ' + game_name)   
    if exact == True:
        bgg_url = BGG_XML_EXACT_SEARCH
    else:    
        bgg_url = BGG_XML_SEARCH    
    try:
        game_url = bgg_url + urllib2.quote(game_name.encode('utf8'))
    except KeyError: # Most likely foreign characters in game_name
        return None    
    logging.info(TRACE+'getBGGMatches():: game_url = ' + game_url) 
    try:
        result = urllib2.urlopen(game_url).read()
    except Exception:
        return None
    xml = ElementTree.fromstring(result)
    try:
        boardgames = xml.findall("./boardgame")            
    except AttributeError:
        logging.info(TRACE+'getBGGMatches():: NO MATCH') 
        return None    
    matches = []
    for x in boardgames:
        game = {"bgg_id": x.attrib['objectid'],
                "name": x.findtext("./name"),
                "year": x.findtext("./yearpublished")}
        matches.append(game)        
    return matches
    
def updateFreebaseBGGID(mid, bgg_id, connect='update'):
    logging.info(TRACE+'updateFreebaseBGGID('+mid+','+bgg_id+')')    
    if bgg_id == "0": return # Don't store 0
    if not FREEBASE.loggedin():
        FREEBASE.login(username=FREEBASE_USER, password=FREEBASE_PSWD)
    query = {
        "type":"/games/game",
        "mid":mid,
        "key":{
            "connect":connect,
            "namespace":BGG_NAMESPACE,
            "value":bgg_id
            }
        }
    try: result = FREEBASE.mqlwrite(query)
    except Exception: return
