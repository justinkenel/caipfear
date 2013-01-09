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
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import template

class Participant(db.Model):
	added = db.DateTimeProperty(auto_now_add=True)
	id = db.IntegerProperty(required=True)
	
class Fear(db.Model):
	added = db.DateTimeProperty(auto_now_add=True)
	name = db.StringProperty(required=True)
	description = db.StringProperty(required=True)
	avoid = db.StringProperty(required=True)
	participant = db.ReferenceProperty(reference_class=Participant, required=True)
	
	updates = None
	value = None
	docname = None
	
	def find_updates(self):
		self.updates = Update.all().filter('fear =', self).order('-added').fetch(limit=100)
		self.value = self.updates[0].value
		self.docname = self.name.replace(' ', '_')
		
		return self
	
class Update(db.Model):
	added = db.DateTimeProperty(auto_now_add=True)
	value = db.IntegerProperty(required=True)
	fear = db.ReferenceProperty(reference_class=Fear, required=True)
	
class MainHandler(webapp.RequestHandler):
	def get(self):
		user=users.get_current_user()
		if not user or not users.is_current_user_admin():
			return self.redirect(users.create_login_url('/'))
			
		pid = self.request.get('participant-id')
		
		if not pid:
			return self.response.out.write(template.render('load.html', {}))
		else:
			pid = int(pid)
		
		participant = Participant.all().filter('id =', int(pid)).get()
		
		if not participant:
			newparticipant = self.request.get('new-participant')
		
			if not newparticipant:
				values = {'pid':pid}
				return self.response.out.write(template.render('new.html', values))
			
			participant = Participant(id = int(pid))
			participant.put()
			
		newfear = self.request.get('new-fear')
		
		if newfear:
			fearname = self.request.get('fear-name')
			feardescription = self.request.get('fear-description')
			fearavoid = self.request.get('fear-avoid')
			
			fearvalue = self.request.get('fear-value')
			
			if not (fearname and feardescription and fearavoid and fearvalue):
				pass
				
			fear = Fear.all().filter('name =', fearname).filter('participant =', participant).get()
			if not fear:
				fear = Fear(name=fearname, description=feardescription, avoid=fearavoid, participant=participant)
				fear.put()
				
				update = Update(value=int(fearvalue), fear=fear)
				update.put()
			else:
				pass
			
		updatefear = self.request.get('update-fear')
		
		if updatefear:
			fearname = self.request.get('fear-name')
			pid = self.request.get('participant-id')
			if not (fearname and pid):
				pass
			
			value = self.request.get('update-%s' % fearname)
			if not value:
				pass
			
			value = int(value)
			participant = Participant.all().filter('id =', int(pid)).get()
			fear = Fear.all().filter('name =', fearname).filter('participant =', participant).get()
			
			last_update = Update.all().filter('fear =', fear).order('-added').get()
			
			if value != last_update.value:
				update = Update(value = value, fear=fear)
				update.put()
		
		fears = map(lambda x:x.find_updates(), Fear.all().filter('participant =', participant))
		
		values = {
			'pid':pid,
			'fears':fears
		}
		
		return self.response.out.write(template.render('main.html', values))
		
	def post(self):
		return self.get()

def main():
	application = webapp.WSGIApplication([('/', MainHandler)],
                                         debug=True)
	util.run_wsgi_app(application)

if __name__ == '__main__':
	main()
