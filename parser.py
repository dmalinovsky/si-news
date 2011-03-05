#!/usr/bin/python
# coding=utf-8
import cPickle as pickle
import json
from PyQt4 import QtCore
from PyQt4 import QtNetwork
import urllib2

from pyquery import PyQuery as pq

# Index page for author stories
STORY_INDEX = 'indexdate.shtml'
# File name with list of friends
CFG_FRIENDS = 'friends.cfg'
# File name with list of stories
CFG_STORIES = 'stories.cfg'


class Parser(object):
    '''Class with static methods only to enable external API.'''
    _friends = None
    _data = None
    _network = None
    _callback = None

    @classmethod
    def get_friends(cls):
        '''Returns friend links list. None if not found.'''
        if cls._friends is None:
            cls._friends = cls.load_data(CFG_FRIENDS)
            if cls._friends is None:
                cls._friends = []
        return cls._friends

    @classmethod
    def get_stories(cls):
        if cls._data is None:
            cls._data = cls.load_data(CFG_STORIES, False)
            if cls._data is None:
                cls._data = ({}, [])
        return cls._data

    @classmethod
    def update_author(cls, url, callback):
        """
        We're assuming callback is the same all the time.
        """
        if cls._network is None:
            cls._network = QtNetwork.QNetworkAccessManager()
            cls._network.finished.connect(cls.on_update_author)
        cls._callback = callback
        if not url.endswith(STORY_INDEX):
            if not url.endswith('/'):
                url += '/'
            url += STORY_INDEX
        cls._network.get(QtNetwork.QNetworkRequest(QtCore.QUrl(url)))

    @classmethod
    def on_update_author(cls, reply):
        """
        Processes finished QNetworkReply, sends list of stories to callback (or
        False on error).
        """
        if reply.error():
            print reply.errorString()
            stories = False
        else:
            content = reply.readAll()
            content = cls.parse_page(content, str(reply.url().toString()))
            stories = {}
            for a in content('li > a > b').parent():
                desc = pq(a).parent().parent().parent()('dd').eq(0).text()
                stories[a.get('href')] = pq(a).text(), a.getnext().text, desc
        cls._callback(stories)

    @classmethod
    def load_data(cls, fname, use_json=True):
        """
        Tries to load serialized Python data from file or return None on failure.
        """
        try:
            f = open(fname, 'rb')
        except IOError:
            return None
        if use_json:
            data = json.load(f)
        else:
            data = pickle.load(f)
        f.close()
        return data

    @classmethod
    def store_data(cls, fname, data, use_json=True):
        '''Stores serialized Python data into specified file.'''
        f = open(fname, 'wb')
        if use_json:
            json.dump(data, f, indent=2)
        else:
            pickle.dump(data, f)
        f.close()

    @classmethod
    def parse_page(cls, raw_content, url):
        """Wraps page text in PyQuery."""
        page = pq(unicode(raw_content, 'cp1251'))
        page.make_links_absolute(base_url=url)
        return page

    @classmethod
    def save_stories(cls, stories, new_urls):
        cls.store_data(CFG_STORIES, (stories, new_urls), False)

    @classmethod
    def get_page(cls, url):
        '''Returns page PyQuery object.'''
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        f = opener.open(url)
        return cls.parse_page(f.read(), url)

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
