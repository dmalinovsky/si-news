#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from collections import OrderedDict, namedtuple
import ConfigParser
from datetime import datetime, timedelta
import json
import logging
import os
import urllib2
import webbrowser

from dateutil.parser import parse
from pyquery import PyQuery as pq
from pytz import timezone


# Folder to store all configuration
HOMEDIR = os.path.expanduser(os.path.join('~', '.si_news'))
if not os.path.isdir(HOMEDIR):
    os.mkdir(HOMEDIR)

# File name with list of friends
CFG_FRIENDS = os.path.join(HOMEDIR, 'friends.cfg')
# Various GUI settings, currently stores friends page URL only
CFG_GUI = os.path.join(HOMEDIR, 'si.ini')
UPDATES_FILE = os.path.join(HOMEDIR, 'updates.html')

LOG_URL = 'http://samlib.ru/logs/%Y/%m-%d.log'
TIMEZONE = timezone('Europe/Moscow')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

LogLine = namedtuple('LogLine', 'url, tag, timestamp, title, author, type, genre, desc, date, img_cnt, update_time, size')


class LastUpdatedOrderedDict(OrderedDict):
    'Store items in the order the keys were last added'

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)


class Parser(object):
    '''Class with static methods only to enable external API.'''
    _friends = None

    @classmethod
    def get_friends(cls):
        '''Returns friend links list. None if not found.'''
        if cls._friends is None:
            cls._friends = cls.load_data(CFG_FRIENDS)
            if cls._friends is None:
                cls._friends = []
        cls._friends = {'/' + x[0].split('/', 3)[3] for x in cls._friends}
        return cls._friends

    @classmethod
    def load_data(cls, fname):
        """
        Tries to load serialized Python data from file or return None on failure.
        """
        try:
            f = open(fname, 'rb')
        except IOError:
            return None
        data = json.load(f)
        f.close()
        return data

    @classmethod
    def store_data(cls, fname, data):
        '''Stores serialized Python data into specified file.'''
        f = open(fname, 'wb')
        json.dump(data, f, indent=2)
        f.close()

    @classmethod
    def parse_page(cls, raw_content, url):
        """
        Wraps page text in PyQuery.
        Returns False on error.
        """
        try:
            page = pq(unicode(raw_content, 'cp1251'))
        except SyntaxError:
            print 'Parser error on %s' % url
            return False
        page.make_links_absolute(base_url=url)
        return page

    @classmethod
    def get_page(cls, url):
        '''Returns page PyQuery object.'''
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        logging.debug('Opening %s...', url)
        try:
            f = opener.open(url)
        except urllib2.HTTPError:
            print 'HTTP error for %s' % url
            raise
        res = cls.parse_page(f.read(), url)
        logging.debug('Done')
        return res

    @classmethod
    def get_friend_links(cls, url):
        """Also saves fetched links on the disk."""
        page = cls.get_page(url)
        links = []
        for td in page('table[align=right] td table td'):
            td = pq(td)
            # Filter links when I'm a friend
            if td.text().startswith('FRIEND OF: '):
                break
            a = td('a')
            if not a:  # Skip text cells
                continue
            a = a[0]
            links.append((a.get('href'), a.text))
        cls.store_data(CFG_FRIENDS, links)
        return links

    @classmethod
    def read_options(cls):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(CFG_GUI)
        try:
            friends_url = cfg.get('DEFAULT', 'friends_url')
        except ConfigParser.NoOptionError:
            friends_url = ''

        try:
            last_updated = cfg.get('DEFAULT', 'last_updated')
        except ConfigParser.NoOptionError:
            last_updated = None

        return friends_url, last_updated

    @classmethod
    def write_options(cls, friends_url, last_updated):
        cfg = ConfigParser.SafeConfigParser()
        cfg.set('DEFAULT', 'friends_url', friends_url)
        cfg.set('DEFAULT', 'last_updated', last_updated.isoformat())
        with open(CFG_GUI, 'w') as cfg_file:
            cfg.write(cfg_file)

    @classmethod
    def load_updates(cls, friends, dt):
        url = dt.strftime(LOG_URL)
        try:
            page = cls.get_page(url)
        except urllib2.HTTPError as e:
            logging.error("Can't open page: %s", e)
            return {}

        lines = page.text().splitlines()
        updates = LastUpdatedOrderedDict()
        for line in lines:
            try:
                log = LogLine._make(line.split('|'))
            except TypeError:
                logging.debug('Invalid format of %s', line)
                continue
            author = log.url.rsplit('/', 1)[0] + '/'
            if author in friends:
                updates[log.url] = log

        return updates

    @classmethod
    def generate_html(cls, updates, now):
        html = '<html><head><base href="http://samlib.ru/"><meta charset="utf-8"></head><body style="background-color:#e9e9e9;">'
        for up in reversed(updates.values()):
            ts = parse(up.timestamp).replace(tzinfo=TIMEZONE)
            if now - ts < timedelta(days=1):
                since = ts.strftime('%H:%M')
            else:
                since = ts.strftime('%d/%m')
            html += """
            <p>
            <li>{0}
            <a href=""><font color=#555555>{author}:</font></a>
            <a href="{url}.shtml"><b>{title}</b></a> &nbsp;
            <b>{size}</b> &nbsp;
            <small> "{type}" {genre}</small>
            <br><dd><font color="#555555">{desc}</font></dd>
            </p>
            """.format(since, **up._asdict())
        html += '</body></html>'
        with open(UPDATES_FILE, 'wb') as fp:
            fp.write(html.encode('utf8'))

        try:
            wb = webbrowser.get('safari')
        except webbrowser.Error:
            logging.debug("Can't find Safari browser, falling back to default")
            wb = webbrowser

        wb.open_new_tab('file://%s' % UPDATES_FILE)


friends_url, last_updated = Parser.read_options()
#Parser.get_friend_links('http://samlib.ru/cgi-bin/frlist?DIR=m/malinowskij_d')
friends = Parser.get_friends()
assert friends, 'Friend list is empty'

now = datetime.now(TIMEZONE)
if last_updated:
    start_date = parse(last_updated)
else:
    start_date = now - timedelta(days=14)
updates = LastUpdatedOrderedDict()
while start_date < now:
    day_updates = Parser.load_updates(friends, start_date)
    for url, up in day_updates.iteritems():
        if up.tag == 'DEL':
            if url in updates:
                del updates[url]
        else:
            updates[url] = up
    logging.info('%d new updates, %d total', len(day_updates), len(updates))
    start_date += timedelta(days=1)

start_date = now
Parser.write_options(friends_url, start_date)
Parser.generate_html(updates, now)
