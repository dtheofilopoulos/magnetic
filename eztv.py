#!/usr/bin/env python
#coding = utf8
import os.path, subprocess, time, urllib2, feedparser

os.system("clear")

###  COLORED OUTPUT  ##############################################################################
AEC = {"BLD":"\033[1m", "RED":"\033[91m", "YLW":"\033[93m", "RST":"\033[0m",}

###  CREDITS  #####################################################################################
MODTIME = os.path.getmtime(__file__)
PRONAME = os.path.basename(__file__)
VERSION = "v4.4"

print(u"""
 {BLD}""" + PRONAME + """, """ + VERSION + """{RST} | EZTV Torrent Downloader

	Downloads matching TV Series titles as soon as they air on eztv
	and automatically queues them to a running transmission daemon

	License  | Dio ( classicrocker384@gmail.com ), 3-Clause BSD License
	Revision | """ + str(time.strftime('%d/%m/%Y, %H:%M', time.localtime(MODTIME))) + """
	Depends  | transmission-remote,
	           os.path, subprocess, time, urllib2, feedparser
	
 ------------------------------------------------------------------------------
""").format(**AEC)

###  CONFIGURATION  ###############################################################################
DIRECTORY = os.path.dirname(__file__) + "/pyEZTV/"	# Absolute PATH of working directory
WATCHLIST = DIRECTORY + "series.db"			# TV SERIES watchlist
HASHESLOG = DIRECTORY + "torrent.log"			# History log of matched torrents w/ hashes
TORRENTDB = DIRECTORY + "torrent.db"			# Matched torrents database w/ magnet links

###  SETTINGS  ####################################################################################
RSSXMLURI = "https://eztv.io/ezrss.xml"			# RSS2.0 XML URI
TOR_WRITE = "ON"					# Keep magnet URIs in Torrent DB   [ON|OFF]
LOG_WRITE = "ON"					# Keep torrents in history log     [ON|OFF]
DAYS2KEEP = "2"						# Clean history log after x days
FILTER_TR = "ON"					# Activate filter (needs FILTERSTR)[ON|OFF]
FILTERSTR = "480p, 720p, 1080p, .avi$, iP.WEB-DL"	# Do NOT download FILENAMES w/ these tags

###  TRANSMISSION DAEMON  #########################################################################
ADDMAGNET = "ON"					# Add magnet URIs to transmission  [ON|OFF]
TRAN_HOST = "192.168.2.100"				# Transmission Daemon Host
TRAN_PORT = "9091"					# Transmission Daemon Port
USERNAME = "transmission"				# Transmission Daemon Username
PASSWORD = "transmission"				# Transmission Daemon Password

###  DEFINE VARIABLES  ############################################################################
TVSERIESDB = []
TORRENT_DB = []
HISTORYLOG = []
TORRENTSDT = {}
WATCH_SIZE = "0"
FILTER_SPC = "0"


###  Create data directory for the script if it does not exist
if (not os.path.exists(DIRECTORY)):
	os.makedirs(DIRECTORY)

###  Print the WATCHLIST
print(u" :::  {BLD}TV SERIES WATCHLIST{RST}  ::::::::::::::::::::::::::::::::::::::::::::::::::::").format(**AEC)
try:
	LIST = open(WATCHLIST, "r")
	for SERIES in sorted(LIST):
		SERIES = SERIES.strip()
		if len(SERIES):
			WATCH_SIZE = "1"			
			###  Make the TITLES lowercase for easier comparison
			TVSERIESDB.append(SERIES.lower())
		LIST.close()
	print(u"")
	
	### need to revisit this bit of code at some point...
	if (WATCH_SIZE == "1"):
		subprocess.call("more -scfl " + str(WATCHLIST) + " | sort -ubdfV | cut -c -17 | sed -e 's/^/      /g' | column -c 74",shell=True)
	
	else:
		print(u"     {BLD}{YLW} \u26a0 \33[39m" + WATCHLIST + " is {YLW}EMPTY{RST}").format(**AEC)
		print(u"     {BLD}{YLW} \u26a0 ADD\33[39m TV series titles, separated by a new line (e.g. Family Guy)").format(**AEC)
	print(u"")
	
except IOError:
	print(u"\n     {BLD}{RED} \u2716 \33[39m" + WATCHLIST + " {RED}NOT ACCESSIBLE{RST}").format(**AEC)
	open(WATCHLIST, "w").close()
	print(u"     {BLD}{RED} \u2716 \33[39m" + WATCHLIST + " was CREATED{RST}\n").format(**AEC)


###  if HASHESLOG has not been modified for more than x days, start CLEAN
if (LOG_WRITE == "ON"):
	try:
		CUR_TIME = time.time()
		MOD_TIME = os.path.getmtime(HASHESLOG)
	
		if (CUR_TIME - MOD_TIME >= DAYS2KEEP * 24 * 3600):
			
			open(HASHESLOG, "w").close()
			print(u"     {BLD}{YLW} \u26a0 \33[39m" + HASHESLOG + " was TRUNCATED{RST}").format(**AEC)
		
	except:
		print(u"     {BLD}{RED} \u2716 \33[39m" + HASHESLOG + " was {RED}NOT ACCESSIBLE{RST}").format(**AEC)
		open(HASHESLOG, "w").close()
		print(u"     {BLD}{RED} \u2716 \33[39m" + HASHESLOG + " was CREATED{RST}\n").format(**AEC)


print(u"\n :::  {BLD}TV SERIES MATCHES{RST}  ::::::::::::::::::::::::::::::::::::::::::::::::::::::\n").format(**AEC)
###  Check the EZTV RSS2.0 URI and parse the XML
try:
	URIHEADER = { "User-Agent": "Links (2.7; Linux; text)", "Content-Type": "text/xml", "pragma-directive": "no-cache" }
	XML = urllib2.urlopen(urllib2.Request(RSSXMLURI, headers=URIHEADER), timeout=15)
	
	###  Parse the XML for a limit of 50 entries
	XML_PARSED = feedparser.parse(XML).entries[:50]
	
except:
	print(u"     {BLD}{RED} \u2716 \33[39mHTTP STATUS {RED}408\33[39m for URI " + str(RSSXMLURI) + "{RST}").format(**AEC)


try:
	for XMLENTRY in XML_PARSED:
		
		###  FETCH RSS VARIABLES
		XMLTITLE = str(XMLENTRY.title)
		XML_FILE = str(XMLENTRY.torrent_filename)
		XML_HASH = str(XMLENTRY.torrent_infohash)
		XML_MAGN = str(XMLENTRY.torrent_magneturi)			
		
		for SERIES in TVSERIESDB:
			
			###  make EZTV SERIES TITLES lowercase for easier comparison
			if (SERIES.lower() in XMLTITLE.lower()):
				
				###  DO NOT download FILTERED names (using filename for consistency reasons)
				if (FILTER_TR == "ON"):
					if (any(FILTER in XML_FILE for FILTER in FILTERSTR)):
						FILTER_SPC = "1"
						print(u"      {BLD}{YLW}\u26a0 {YLW}FILTERED{RST} : " + XML_FILE).format(**AEC)[:95] + " ..."
						continue
				
				###  in the off-chance that NO MAGNET URI in the XML, filter out the problematic torrent
				if (XML_MAGN == ""):
					print(u"      {BLD}{RED}\u2716 {YLW}NO MAGNET URI{RST} : " + XML_FILE).format(**AEC)[:95] + " ..."
					continue
				
				###  Load historical hashes
				HISTORY = open(HASHESLOG, "r")
				for HASH in HISTORY:
					HASH = HASH.strip()
					if len(HASH):
						HISTORYLOG.append(HASH)
				HISTORY.close()
				
				###  Check the HISTORY LOG for already downloaded torrents
				if (XML_HASH in HISTORYLOG):
					continue
				else:
					HISTORYLOG.append(XML_HASH)
				
				###  Check for existing MAGNET LINKS
				if (XML_MAGN in TORRENT_DB):
					continue
				else:
					TORRENT_DB.append(XML_MAGN)
				
				###  Build the array with UNIQUE torrent matches based on infohash
				TORRENTSDT[XML_HASH] = { "TITLE": XMLTITLE, }
	
	
	###  WRITE LOGS FOR MATCHED TORRENTS
	LOGRESULTS = []
	for TOR in TORRENTSDT:
		### Write the TORRENT LOG. Append MAGNET URIs for MATCHED TORRENTS
		if (TOR_WRITE == "ON"):
			try:
				MAGNETDB = open(TORRENTDB, "w")
				for MAGNETURI in TORRENT_DB:
					MAGNETDB.write(MAGNETURI + "\n")
				MAGNETDB.close()
			
			except IOError:
				quit(u"     {BLD}{RED} \u2716 \33[39m" + TORRENTDB + " was {RED}NOTT ACCESSIBLE{RST}").format(**AEC)
			
			
		### Write the HISTORY LOG. We DO NOT WANT to DOWNLOAD torrents twice
		if (LOG_WRITE == "ON"):
			try:
				LOGDB = open(HASHESLOG, "w")
				for HASH in HISTORYLOG:
					LOGDB.write(HASH + "\n")
				LOGDB.close()
			
			except IOError:
				quit(u"     {BLD}{RED} \u2716 \33[39m" + HASHESLOG + " was {RED}NOT ACCESSIBLE{RST}").format(**AEC)
		
		###  TITLES of TORRENT DOWNLOADS
		LOGRESULTS.append(TORRENTSDT[TOR]["TITLE"])
		

	###  PRINT TV SERIES MATCHES
	if (FILTER_TR == "ON" and FILTER_SPC == "1"):
		print(u"")
	
	if LOGRESULTS:
		print(u"     {BLD}{RED} " + str(len(LOGRESULTS)) + " \33[39mTORRENTS{RST} match your TV series watchlist\n").format(**AEC)
		i = 1
		for RESULT in LOGRESULTS:
			print(u"      {BLD}" + str(i).zfill(2) + "{RST}. " + RESULT).format(**AEC)
			i += 1
		print(u"")
	else:
		print(u"     {BLD}{YLW} \u26a0 NO \33[39mTORRENTS{RST} match your TV series watchlist criteria").format(**AEC)


except:
	print(u"     {BLD}{RED} \u2716 CANNOT{RST} match torrents").format(**AEC)


###  TRANSMISSION REMOTE
if (ADDMAGNET == "ON"):
	
	TRANSMISSION_REMOTE = subprocess.call(["which", "transmission-remote"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	
	if (TRANSMISSION_REMOTE != 0):
		quit(u"\n     {BLD}{RED} \u2716 \33[39mtransmission-remote is {RED}MISSING{RST}. Install before continuing.\n").format(**AEC)
		
	else:
		try:
			subprocess.check_call("nc -w 3 -vz " + TRAN_HOST + " " + TRAN_PORT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
			if (os.path.getsize(TORRENTDB) > 0):
				MAGNETDB = open(TORRENTDB, "r")
				for TORR in MAGNETDB:
					TORR = TORR.strip()
					if len(TORR):
						TRANSMISSION = "transmission-remote " + TRAN_HOST + ":" + TRAN_PORT + " --auth " + USERNAME + ":" + PASSWORD + " --add " + TORR
						subprocess.call(TRANSMISSION,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
						
					###  Clear the magnet links database
					open(TORRENTDB, "w").close()
				MAGNETDB.close()
			
				print(u"     {BLD} TORRENTS {RED}ADDED\33[39m to Transmission BT Daemon{RST}").format(**AEC)	
		
		except:
			quit(u"     {BLD}{RED} \u2716 {RST}Could NOT connect to Transmission. Check RPC configuration.\n").format(**AEC)

### QUIT EVERYTHING, JUST IN CASE
quit(u"\n")

#
# EOF
#
