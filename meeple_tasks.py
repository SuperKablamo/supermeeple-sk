#
# Copyright 2010 SuperKablamo, LLC
# info@superkablamo.com
#

############################# IMPORTS ########################################
############################################################################## 
import freebase
import logging
import models
import urllib2

from settings import *
from urlparse import urlparse
from xml.etree import ElementTree 
from django.utils import simplejson
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

############################# REQUEST HANDLERS ############################### 
##############################################################################   
class FreebaseCursor(db.Model):
    cursor = db.StringProperty(required=True)
    created = db.DateTimeProperty(required=True, auto_now=True)

class GameBuilder(webapp.RequestHandler):
    def get(self):
        logging.info('################# GameBuilder:: get ##################')

    def post(self, )
    
                                                
class Admin(BaseHandler):
    def get(self, pswd=None):
        logging.info('################### Admin:: get() ####################')
        logging.info('################### pswd =' +pswd+ ' #################')        
        if pswd == "backyardchicken":
            badges = getBadges()
            image_upload_url = blobstore.create_upload_url('/upload/image')
            thumb_upload_url = blobstore.create_upload_url('/upload/thumb')
            template_values = {
                'badges': badges,
                'image_upload_url': image_upload_url,
                'thumb_upload_url': thumb_upload_url,
                'current_user': self.current_user,
                'facebook_app_id': FACEBOOK_APP_ID
            }  
            self.generate('base_admin.html', template_values)
        else: self.redirect(500)  
        
    def post(self, method=None):
        logging.info('################### Admin:: post() ###################')
        logging.info('################### method =' +method+' ##############')
        if method == "create-badges":
            createBadges()
        elif method == "build-games":
            taskqueue.add(url='/build-games')
        self.redirect('/admin/backyardchicken')  
    
  
  
######################## METHODS #############################################
##############################################################################
  
##############################################################################
##############################################################################
application = webapp.WSGIApplication([('/_ah/queue/build-games', GameBuilder)],
                                       debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
