# ============================================================================
# Copyright (c) 2011, SuperMeeple, LLC.
# All rights reserved.
# info@supermeeple.com
#
# ============================================================================

############################# IMPORTS ########################################
############################################################################## 
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

from google.appengine.api import memcache
from google.appengine.ext import db

############################# METHODS ########################################
##############################################################################

def getGame(mid, bgg_id='0'):
    """Returns a Game.  Looks for one in memcache, if not then creates one
    using the BGG XML API.
    """
    logging.info(TRACE+'getGame('+bgg_id+', '+mid+')')
    if mid is None: return None
    game_cache = memcache.get(mid)
    if game_cache is None: # If this Game is not cached, build a new cache
        game = models.Game.get_by_key_name(mid)
        
        if game is None: # Game has never been stored, so build and store it.
            if bgg_id == '0': # No BGG ID, return FB data
                game = buildFBGame(mid)
            else: # BGG ID, return BGG data 
                game_data = parseBGGXML(bgg_id) # Refresh stored XML
                if game_data is None: # If BGG is down, use FB
                    logging.info(TRACE+'getGame():: BGG error, using FB')
                    game = buildFBGame(mid)
                else: # Build Game from BGG data
                    game = models.Game(key_name=mid,
                                 mid=mid,
                                 bgg_id=bgg_id,
                                 bgg_img_url=game_data['image_url'],
                                 bgg_thumbnail_url=game_data['thumbnail_url'],
                                 name=game_data['name'],
                                 description=game_data['description'],
                                 year_published = game_data['year_published'],
                                 min_players = game_data['min_players'],
                                 max_players = game_data['max_players'],
                                 playing_time = game_data['playing_time'],
                                 age = game_data['age'],
                                 publishers = game_data['publishers'],
                                 artists = game_data['artists'],
                                 designers = game_data['designers'],
                                 expansions = game_data['expansions'],
                                 categories = game_data['categories'],
                                 mechanics = game_data['mechanics'],
                                 subdomains = game_data['subdomains'])
                
                    # Store BGG XML 
                    game_xml = models.GameXML.get_by_key_name(bgg_id)
                    if game_xml is None:
                        game_xml = models.GameXML(key_name=bgg_id, 
                                                  xml=game_data['xml_text'])  
                    else:
                        game_xml.xml = game_data['xml_text']                 
                    # Save Game and GameXML, and then create Cached Game
                    game.put()
                    game_xml.put()       
                    success = memcache.set(key=mid, 
                                           value=game, 
                                           time=432000) # expiration 5 days
        
        else: # Game has been stored, get it, update data.
            logging.info(TRACE+'getGame() bgg_id = '+bgg_id)
            if bgg_id != '0': # There is a BGG connection . . . 
                game_xml = models.GameXML.get_by_key_name(bgg_id)
                # Use BGG XML API to get Game data
                game_data = parseBGGXML(bgg_id)
                if game_data is None: # If BGG is down, use FB
                    logging.info(TRACE+'getGame():: BGG error, using FB')
                    game = buildFBGame(mid)
                else:                
                    # Build Game from BGG data            
                    game.name = game_data['name']
                    game.bgg_id = bgg_id
                    game.bgg_thumbnail_url = game_data['thumbnail_url']            
                    game.bgg_img_url = game_data['image_url']
                    game.description = game_data['description']
                    game.year_published = game_data['year_published']
                    game.min_players = game_data['min_players']
                    game.playing_time = game_data['playing_time']
                    game.age = game_data['age']
                    game.publishers = game_data['publishers']
                    game.artists = game_data['artists']
                    game.designers = game_data['designers']  
                    game.expansions = game_data['expansions']
                    game.categories = game_data['categories']
                    game.mechanics = game_data['mechanics']
                    game.subdomains = game_data['subdomains']
                    game_xml = models.GameXML.get_by_key_name(bgg_id)
                    if game_xml is None:
                        game_xml = models.GameXML(key_name=bgg_id, 
                                                  xml=game_data['xml_text'])  
                    else:
                        game_xml.xml = game_data['xml_text']
                    game.put() # Save Game
                    game_xml.put() # Save GameXML
                    success = memcache.set(key=mid, 
                                           value=game, 
                                           time=432000) # expiration 5 days
        
        game_cache = game        
    return game_cache

def buildGame(mid, bgg_id):
    """Builds a Game from the BGG XML API.  Expects bgg_id is not None.
    """
    logging.info(TRACE+'buildGame('+str(bgg_id)+', '+str(mid)+')')
    game = models.Game.get_by_key_name(mid)
    if game is None: # Game has never been stored, so build and store it.
        # Use BGG XML API to get Game data
        game_data = parseBGGXML(bgg_id)
        if game_data is None: 
            logging.info(TRACE+'buildGame() failed, unable to parse BGGXML')
            return None
        # Build Game from BGG data
        game = models.Game(key_name=mid,
                           mid=mid,
                           bgg_id=bgg_id,
                           bgg_img_url=game_data['image_url'],
                           bgg_thumbnail_url=game_data['thumbnail_url'],
                           name=game_data['name'],
                           description=game_data['description'],
                           year_published = game_data['year_published'],
                           min_players = game_data['min_players'],
                           playing_time = game_data['playing_time'],
                           age = game_data['age'],
                           publishers = game_data['publishers'],
                           artists = game_data['artists'],
                           designers = game_data['designers'],
                           expansions = game_data['expansions'],
                           categories = game_data['categories'],
                           mechanics = game_data['mechanics'],
                           subdomains = game_data['subdomains'])
        
        game_xml = models.GameXML(key_name = bgg_id, 
                                  xml = game_data['xml_text'])
                                                  
        game.put() # Save Game
        game_xml.put() # Save GameXML  

def buildFBGame(mid):
    """Builds a Game from the Freebase API.  Expects mid is not None.
    """
    fb_game = getFBGame(mid)
    game_data = parseFBJSON(fb_game)
    game_blurb = getFBGameBlurb(mid, 2000)
    if game_blurb is not None:
        game_blurb_text = db.Text(game_blurb.decode("utf-8"))  
    else:
        game_blurb_text = None      
    game = models.Game(key_name=mid,
                     mid=mid,
                     name=game_data['name'],
                     year_published = game_data['year_published'],
                     min_players = game_data['min_players'],
                     max_players = game_data['max_players'],
                     playing_time = game_data['playing_time'],
                     age = game_data['age'],
                     publishers = game_data['publishers'],
                     designers = game_data['designers'],
                     expansions = game_data['expansions'],
                     description = game_blurb_text)
    game.put()
    success = memcache.set(key=mid, 
                           value=game, 
                           time=432000) # expiration 5 days 
    
    return game

def parseBGGXML(bgg_id):
    """Returns a dictionary of game data retrieved from BGGs XML API.
    """
    logging.info(TRACE+'parseBGGXML('+bgg_id+')')
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
    
def getFBGame(mid):
    """Returns a JSON result for Freebase Game data.    
    """
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
      "key" : {
        "namespace" : "/user/pak21/boardgamegeek/boardgame",
        "value" : None,
        "optional": True
      }
    }       
    return FREEBASE.mqlread(query, extended=True)  

def getFBGameBlurb(mid, length=400):
    """Returns a description of the Game.  Freebase stores descriptions in a 
    datastore separate from the rest of the data, and can only be retrieved 
    using the Trans service.
    """
    logging.info(TRACE+'getFBGameBlurb('+mid+', '+str(length)+')')    
    try:
        blurb = FREEBASE.blurb(mid, break_paragraphs=True, maxlength=length)
    except Exception:
        # The Freebase module raises a MetawebError if a blurb is not found
        return None
    return blurb     

def parseFBJSON(json):
    """Returns a dictionary of game data retrieved from Freebase.
    """
    logging.info(TRACE+'parseFBJSON('+str(json)+')')
    fb_data = {'name': json.name}
    if json.introduced is not None: 
        fb_data['year_published'] = strToInt(json.introduced)  
    else: fb_data['year_published'] = None      
    if json["/games/game/number_of_players"] is not None:
        fb_data['min_players'] = strToInt(json["/games/game/number_of_players"].high_value)
        fb_data['max_players'] = strToInt(json["/games/game/number_of_players"].low_value)
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
    
    return fb_data        