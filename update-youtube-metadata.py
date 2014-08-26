# -*- coding: UTF-8 -*-

import youtube_api
from youtube_api import debug
import json
import lxml.etree
import gdata.media
import sys
import getpass

dry_run = True
dry_run = False
#debug = False

#schedule = lxml.etree.parse("http://domain.tld/schedule.xml")
schedule = lxml.etree.parse("schedules/froscon2014.xml")
fahrplan_base_url = 'http://programm.froscon.de/2014/events/'
conference_tags = ['froscon', 'froscon9', 'froscon14', '2014', 'st augustin', 'free and open source conference', 'koeln', 'bonn', 'germany']

def main():
    with open('youtube-urls.json') as data_file:
        videos = json.load(data_file)
    
    if not(dry_run):
        youtube = youtube_setup()
    
    #for event_id, youtube_url in {'61': 'https://www.youtube.com/watch?v=TQcc1ax75xw'}.iteritems():
    for event_id, youtube_url in videos.iteritems():
        #if int(event_id) >= 20:
        #    continue

        print event_id
        print youtube_url
        #print
        
        event = get_event(event_id)
    
        #don't process events, which don't exist in schedule xml
        if event == False: 
            print ' event ' + event_id + ' is not in schedule. ignoring.'
            continue
        
        persons = event.find('persons').getchildren()
        
        title = event.find('title').text
        if len(persons) == 1:
            title = persons[0].text + ': ' + title
        elif len(persons) == 2:
            title = persons[0].text + ', ' + persons[1].text + ': ' + title
        
        # Youtube allows max 100 chars, see https://groups.google.com/d/msg/youtube-api-gdata/RzzD0MxFLL4/YiK83QnS3rcJ
        title = title[:99]
       
	def desc_format(key):
            try:
                return '\n\n' + strip_tags(event.find(key).text.replace('<li>', '* '))
            except:
		return ''
 
        description = fahrplan_base_url + event_id + '.html' + \
            desc_format('abstract') + \
            desc_format('description')
        
        keywords = ', ' . join(conference_tags + [p.text for p in persons])
        
        print title
        #print description
        #print keywords
        print
        
        if not(dry_run):
            #youtube.update_metadata(youtube_url, title, description)
            entry = youtube._get_feed_from_url(youtube_url)
            entry.media.title = gdata.media.Title(text=title)
            entry.media.description = \
                    gdata.media.Description(description_type='plain', text=description) 
            entry.media.keywords = gdata.media.Keywords(text=keywords)
            youtube.service.UpdateVideoEntry(entry)
            
    
    print "success"


def get_event(event_id):
    result = schedule.xpath('day/room/event[@id="' + event_id + '"]')
    if result: 
        return result[0]
    else:
        return False

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def youtube_setup():
    with open('.youtube-login') as fp:
        (email,password) = fp.read().strip().split(':', 1)

    if password is None or password == '':
        password = getpass.getpass("Password for account <%s>: " % email)
    elif password == "-":
        password = sys.stdin.readline().strip()
    youtube = youtube_api.Youtube(youtube_api.DEVELOPER_KEY)
    debug("Login to Youtube API: email='%s', password='%s'" %
          (email, "*" * len(password)))
    try:
        youtube.login(email, password) #, captcha_token=options.captcha_token,
            #       captcha_response=options.captcha_response)
    except gdata.service.BadAuthentication:
        raise youtube_api.BadAuthentication("Authentication failed")
    except gdata.service.CaptchaRequired:
        token = youtube.service.captcha_token
        message = [
            "Captcha request: %s" % youtube.service.captcha_url,
            "Re-run the command with: --captcha-token=%s --captcha-response=CAPTCHA" % token,
        ]
        raise youtube_api.CaptchaRequired("\n".join(message))
    
    return youtube

if __name__ == '__main__':
    main()
