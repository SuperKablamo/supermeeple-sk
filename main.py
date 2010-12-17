#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import cgi
import freebase
import logging

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import models

class MainHandler(webapp.RequestHandler):
    def get(self):
        logging.info('########### MainHandler::get ###########')

        query = [{
          "type" : "/games/game",
          "name" : None,
          "id" : None
        }]
        result = freebase.sandbox.mqlread(query)
        games = result
        template_values = {
            'games': games
        }        

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'index.html'))
        self.response.out.write(template.render(path, template_values, debug=True))
 
class PostGame(webapp.RequestHandler):
    def post(self):
        logging.info('########### GetGame::post ###########')
        gameID = self.request.get('gameID')
        gameName = self.request.get('gameName')
        logging.info('gameID = ' + str(gameID) + 'gameName = ' + str(gameName))

        query = {
          "type" : "/games/game",
          "id" : gameID,
          "name" : None
        }
        result = freebase.sandbox.mqlread(query)
        game = result
        template_values = {
            'game': game
        }

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', 'game.html'))
        self.response.out.write(template.render(path, template_values, debug=True))

application = webapp.WSGIApplication(
                                     [('/', MainHandler),
                                     ('/game-profile', PostGame)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
