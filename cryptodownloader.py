#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

    cryptodownloader.py 0.1

    This tool downloads the video recordings of the lecture "Kryptografie und
    Datensicherheit I and II" in German and English language. You can use "-d"
    as a command line argument to download the files immediately.
    
    (c) 2013 Jan Holthuis by 2013

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

import urllib.request, re, sys, os, html.parser
from itertools import zip_longest

# Load HTML source code
def getHTML(url):
	f = urllib.request.urlopen(url)
	encoding = f.headers.get_content_charset('utf-8')
	body = f.read().decode(encoding)
	return body

def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def sizeFormat(size):
	size = float(size)
	size_units = ["B","KiB","MiB","GiB","TiB"]
	size_unit = 0
	while size>1024 and size_unit<len(size_units):
		size = size/1024
		size_unit += 1
	return "%.2f %s" % (size,size_units[size_unit])


def downloadFile(url, filename):
	u = urllib.request.urlopen(url)
	f = open(filename, 'wb')
	meta = u.info()
	filesize = int(meta.get("Content-Length",0))
	print("Download: %s (%s Bytes / %s)" % (filename, filesize, sizeFormat(filesize)))
	len_filesize = len(str(filesize))
	len_filesize_f = len(str(sizeFormat(filesize)))
	filesize_dl = 0
	block_sz = 8192
	while True:
		buffer = u.read(block_sz)
		if not buffer:
			break
		filesize_dl += len(buffer)
		f.write(buffer)
		progress = filesize_dl * 100. / filesize
		status = "%s (%s Bytes) - %03.2f %%%s" % (sizeFormat(filesize_dl).rjust(len_filesize_f), str(filesize_dl).rjust(len_filesize), progress, " "*10)
		print(status,end='\r')
	print('Datei "%s" (%s) wurde heruntergeladen.%s', (filename, sizeFormat(filesize)," "*30))
	f.close()

if "-d" in sys.argv:
	download = True
else:
	download = False

url = "http://wiki.crypto.rub.de/Buch/movies.php"
def getVideos(url):
	linksite = getHTML(url)
	p1 = re.compile('<h3><a name=[\d]+>Chapter ([\d]+)</a></h3>[\s\n]+<h4>([\w\d\s\(\)\:\-\_\;\,]+)</h4>')
	p2 = re.compile('<li>(DE|EN)<a class="mov[\d]+" href="([\d\w\:\.\/\_\-\%]+)" target="video" .* title="([\d\w\:\.\/\_\s\(\)\,\&\;\-]+)">')
	p3 = re.compile('addVariable\("file","([\d\w\:\.\/\_\-\%]+)"\)')
	h = html.parser.HTMLParser()
	chapters = chunks(p1.split(linksite)[1:],3)
	content = []
	num = {"DE":1, "EN":1}
	for chapter in chapters:
		chaptername = "%s - %s" % (chapter[0].zfill(2), chapter[1])
		print(chaptername)
		videos = []
		for video in p2.finditer(chapter[2]):
			videolang = video.group(1)
			videosite = getHTML(video.group(2))
			videolink = "%s/%s" % (video.group(2).rpartition('/')[0],p3.search(videosite).group(1))
			videoname = "%d - %s" % (num[video.group(1)],h.unescape(video.group(3)))
			videos.append((videoname,videolink,videolang))
			num[video.group(1)] += 1
			print("  %s - %s - %s" % (videolang,videoname,videolink))
		content.append((chaptername, videos))
	return content

videolist = getVideos(url)

if download or (input('Willst du die oben genannten Videos in den Ordner "%s" herunterladen? ' % os.getcwd()).lower() in ["ja", "yes", "ok", "y", "j", "1"]):
	downloadlang = ["DE", "EN"]
	for chapter in videolist:
		os.mkdir(chapter[0])
		os.chdir(chapter[0])
		for (videoname, videolink, videolang) in chapter[1]:
			if videolang in downloadlang:
				downloadFile(videolink, "%s - %s.flv" % (videolang, videoname))
		os.chdir("..")
	print("Alle Videos wurden heruntergeladen.")
	sys.exit(0)
else:
	print("Die Videos werden nicht heruntergeladen.")
	sys.exit(0)
