#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Blackboard-Leecher for Ruhr-University of Bochum 0.1
    (c) 2013 by Jan Holthuis <jan.holthuis@ruhr-uni-bochum.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# CONFIG START

USERNAME = ""
PASSWORD = ""

# CONFIG END

import requests, hashlib, BeautifulSoup, urllib2, urlparse, os, os.path, shutil

def enum(*sequential, **named):
	enums = dict(zip(sequential, range(len(sequential))), **named)
	return type('Enum', (), enums)

class Blackboard(object):
	username = USERNAME
	userpass = PASSWORD
	def __init__(self):
		self._session = None
	def _getContentIdFromUrl(self, url):
		link = urlparse.urlparse(url)
		if link.path == "/webapps/Blackboard/content/listContent.jsp":
			q = urlparse.parse_qs(link.query)
			if q.has_key('content_id'):
				return q['content_id'][0]
		return None
	def login(self):
		m = hashlib.md5()
		m.update(self.userpass)
		payload = {'RU_name': self.username, 'RU_pw': self.userpass, 'RU_md5': m.hexdigest(), 'RU_md5': m.hexdigest().upper()}
		self._session = requests.Session()
		r = self._session.post("https://e-learning.ruhr-uni-bochum.de/bin/bbupdate/logintest.pl", data=payload)
	def getCourses(self):
		payload = {'action': 'refreshAjaxModule', 'modId': '_4_1', 'tabId': '_1_1', 'tab_tab_group_id':'_1_1'}
		r = self._session.get("https://e-learning.ruhr-uni-bochum.de/webapps/portal/execute/tabs/tabAction", params=payload)
		soup = BeautifulSoup.BeautifulSoup(BeautifulSoup.BeautifulSoup(r.text).contents[2].contents[0])
		courses = []
		for a in soup.find("ul").findAll("a"):
			courseid = urlparse.parse_qs(urlparse.urlparse(urllib2.unquote(a['href'].strip().split("&url=")[1])).query)['id'][0]
			course = BlackboardCourseObject(self._session, str(courseid))
			courses.append(course)
		return courses

	def download(self, path="", test=True):
		path = os.path.join(path,"Blackboard")
		if test:
			print path
		else:
			os.mkdir(path)
		for course in self.getCourses():
			course.download(path, test)

class BlackboardCourseObject(object):
	def __init__(self, session, courseid):
		self._content = []
		self._session = session
		self._courseid = courseid
		payload = {'course_id': self._courseid}
		r = self._session.get("https://e-learning.ruhr-uni-bochum.de/webapps/blackboard/content/courseMenu.jsp", params = payload)
		soup = BeautifulSoup.BeautifulSoup(r.text)
		self._name = soup.find(id="courseMenu_link").contents[0]
		for a in soup.find(id="courseMenuPalette_contents").findAll("a"):
			contentid = self._getContentIdFromUrl(a['href'])
			if contentid:
				folder = BlackboardFolderObject(self._session, courseid, contentid)
				self._content.append(folder)
	def download(self, path, test):
		name = self.getName().replace(os.path.sep, "-")
		path = os.path.join(path,name)
		if test:
			print path
		else:
			os.mkdir(path)
		for content in self._content:
			content.download(path, test)
	def _getContentIdFromUrl(self, url):
		link = urlparse.urlparse(url)
		if link.path == "/webapps/blackboard/content/listContent.jsp":
			q = urlparse.parse_qs(link.query)
			if q.has_key('content_id'):
				return q['content_id'][0]
		return None
	def getName(self):
		return self._name
class BlackboardFolderObject(object):
	def __init__(self, session, courseid, contentid):
		self._content = []
		self._session = session
		self._courseid = courseid
		self._contentid = contentid
		payload = {'course_id': self._courseid, 'content_id': self._contentid}
		r = self._session.post('https://e-learning.ruhr-uni-bochum.de/webapps/blackboard/content/listContent.jsp', data = payload)
		soup = BeautifulSoup.BeautifulSoup(r.text)
		self._name = soup.find(id="pageTitleText").span.contents[0]
		for li in soup.find(id="content_listContainer").findAll("li", recursive=False):
			try:
				div = li.find("div")
				if div:
					h3 = div.find("h3")
					if h3:
						a = h3.find("a")
						if a:
							# This is a folder
							contentid2 = self._getContentIdFromUrl(a['href'])
							if contentid2:
								self._content.append(BlackboardFolderObject(self._session, self._courseid, contentid2))
						else:
							attachments = li.find("ul", { "class" : "attachments clearfix" })
							if attachments:
								# This is a file (or multiple)
								for attachment in attachments.findAll("li"):
									attachmentlink = attachment.find("a")
									self._content.append(BlackboardFileObject(self._session, attachmentlink.contents[1].replace("&nbsp;"," ").strip(), attachmentlink['href']))
							else:
								# This is a Text entry
								title = h3.findAll("span")[2].contents[0]
								soup = li.find("div", {"class":"vtbegenerated"})
								self._content.append(BlackboardTextObject(self._session, title, soup))
			except AttributeError:
				pass
	def download(self, path, test):
		name = self.getName().replace(os.path.sep, "-")
		path = os.path.join(path,name)
		if test:
			print path
		else:
			os.mkdir(path)
		for content in self._content:
			content.download(path, test)
	def _getContentIdFromUrl(self, url):
		link = urlparse.urlparse(url)
		if link.path == "/webapps/blackboard/content/listContent.jsp":
			q = urlparse.parse_qs(link.query)
			if q.has_key('content_id'):
				return q['content_id'][0]
		return None
	def getName(self):
		return self._name
class BlackboardFileObject(object):
	def __init__(self, session, filename, filelink):
		self._content = []
		self._session = session
		self._name = filename
		self._link = "https://e-learning.ruhr-uni-bochum.de"+filelink
	def download(self, path, test):
		name = self.getName().replace(os.path.sep, "-")
		path = os.path.join(path,name)
		if test:
			print path
		else:
			r = self._session.get(self._link, stream=True)
			f = open(path, 'wb')
			shutil.copyfileobj(r.raw, f)
			f.close()
	def getName(self):
		return self._name
class BlackboardTextObject(object):
	def __init__(self, session, title, text):
		self._content = []
		self._session = session
		self._name = title
		self.stripTags(text, ['span'])
		self._text = text.prettify()
	def stripTags(self, soup, invalid_tags):
		for tag in soup.findAll(True):
			for attribute in ["class", "id", "name", "style"]:
				del tag[attribute]
			if tag.name in invalid_tags:
				s = ""
				for c in tag.contents:
					if not isinstance(c, BeautifulSoup.NavigableString):
						c = self.stripTags(unicode(c), invalid_tags)
					s += unicode(c)
				tag.replaceWith(s)
	def download(self, path, test):
		name = self.getName().replace(os.path.sep, "-")+".html"
		path = os.path.join(path,name)
		if test:
			print path
		else:
			f = open(path, 'wb')
			f.write("<html><body>%s</body></html>" % self._text)
			f.close()
	def getName(self):
		return self._name
b = Blackboard()
b.login()
b.download(test=False)

