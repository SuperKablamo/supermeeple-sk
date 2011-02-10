#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import freebase
import logging
import main
import models
import urllib2

from google.appengine.ext import db
from settings import *
from utils import strToInt
from utils import buildDataList
from utils import findPrimaryName
from xml.etree import ElementTree 

############################# METHODS ########################################
##############################################################################

def buildGame(mid, bgg_id):
    """Builds a Game from the BGG XML API.
    """
    logging.info('######### buildGame('+str(bgg_id)+', '+str(mid)+') #######')
    game = models.Game.get_by_key_name(mid)
    if game is None: # Game has never been stored, so build and store it.
        # Use BGG XML API to get Game data
        game_data = parseBGGXML(bgg_id)
        if game_data is None: 
            logging.info('#### buildGame failed, unable to parse BGGXML ####')
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

def parseBGGXML(bgg_id):
    """Returns a dictionary of game data retrieved from BGGs XML API.
    """
    logging.info("########### parseBGGXML("+bgg_id+") ################")
    bgg_game_url = BGG_XML_URI + bgg_id
    result = urllib2.urlopen(bgg_game_url).read()
    try:
        xml = ElementTree.fromstring(result)
    except Exception:
        logging.info("################## error parsing BGG #################")
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
    logging.info('############ getBGGIDFromBGG:: finding bgg_id ############')
    logging.info('########### game_name = ' + game_name + ' ################')   
    try:
        game_url = BGG_XML_SEARCH + urllib2.quote(game_name.encode('utf8'))
    except KeyError: # Most likely foreign characters in game_name
        return None    
    logging.info('########### game_url = ' + game_url + ' ##################') 
    try:
        result = urllib2.urlopen(game_url).read()
    except Exception:
        return None
    xml = ElementTree.fromstring(result)
    try:
        bgg_id = xml.find("./boardgame").attrib['objectid']
    except AttributeError:
        logging.info('################# NO MATCH ###########################') 
        return None    
    logging.info('################# MATCH FOUND! ###########################')         
    logging.info('########### bgg_id = ' + str(bgg_id) + ' #################') 
    return bgg_id
    
def storeBGGIDtoFreebase(mid, bgg_id):
    logging.info('############ putBGGIDtoFreebase('+mid+','+bgg_id+') ######')    
    if not FREEBASE.loggedin():
        FREEBASE.login(username=FREEBASE_USER, password=FREEBASE_PSWD)
    query = {
        "type":"/games/game",
        "mid":mid,
        "key":{
            "connect":"insert",
            "namespace":BGG_NAMESPACE,
            "value":bgg_id
            }
        }
    result = FREEBASE.mqlwrite(query)
    logging.info('############# mqlwrite result = '+str(result)+ ' #########')    