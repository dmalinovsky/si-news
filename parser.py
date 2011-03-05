#!/usr/bin/python
# coding=utf-8
"""
Requirements: python-pyquery, python-qt4

friends.cfg format:
    ((author_url, author_name), ...)
stories.cfg format:
    ({author_url: {story_url: (title, size, desc), ...}, ...}, [new_url1, ...])
"""
import cPickle as pickle
import json
from PyQt4 import QtCore
from PyQt4 import QtNetwork
import urllib2

from pyquery import PyQuery as pq

# SI friends page
FRIENDS_PAGE = 'http://zhurnal.lib.ru/cgi-bin/frlist?DIR=m/malinowskij_d'
# Delay between requests, in seconds.
REQUEST_DELAY = 1
# Index page for author stories
STORY_INDEX = 'indexdate.shtml'
# File name with list of friends
CFG_FRIENDS = 'friends.cfg'
# File name with list of stories
CFG_STORIES = 'stories.cfg'


def get_page(url):
    '''Returns page PyQuery object.'''
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    f = opener.open(url)
    page = unicode(f.read(), 'cp1251')
    page = pq(page)
    page.make_links_absolute(base_url=url)
    # Make a pause to ease a burden on servers
    QtCore.QThread.sleep(REQUEST_DELAY)
    return page


def get_friend_links():
    page = get_page(FRIENDS_PAGE)
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
    return links


def get_stories(url):
    '''
    Returns dictionary of author stories in following format:
    {url: (title, size, desc), ...}
    '''
    if not url.endswith(STORY_INDEX):
        if not url.endswith('/'):
            url += '/'
        url += STORY_INDEX
    page = get_page(url)
    stories = {}
    for a in page('li > a > b').parent():
        desc = pq(a).parent().parent().parent()('dd').eq(0).text()
        stories[a.get('href')] = pq(a).text(), a.getnext().text, desc
    return stories


def load_data(fname, use_json=True):
    '''
    Tries to load serialized Python data from file or return None on failure.
    '''
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


def store_data(fname, data, use_json=True):
    '''Stores serialized Python data into specified file.'''
    f = open(fname, 'wb')
    if use_json:
        json.dump(data, f, indent=2)
    else:
        pickle.dump(data, f)
    f.close()


def print_story(url, title, size, desc):
    '''Prints story entry.'''
    print "\t%s %s [%s]" % (title, size, url)
    if desc:
        print desc


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
    def save_friends(cls, friends):
        cls.store_data(CFG_FRIENDS, friends)
        cls._friends = friends

    @classmethod
    def update_stories(cls):
        links = cls.get_friends()
        stories, _ = cls.get_stories()
        new_stories = {}
        new_urls = []
        # Load new stories and compare with saved ones
        for author_url, author_name in links:
            print "%s [%s]" % (author_name, author_url)
            author_stories = get_stories(author_url)
            new_stories[author_url] = author_stories
            if author_url not in stories:
                continue  # We just imported new author
            for url, story in author_stories.iteritems():
                if (url not in stories[author_url] or
                        stories[author_url][url] != story):
                    new_urls.append(url)
                    print_story(url, *story)

        # Store loaded data
        cls.store_data(CFG_STORIES, (new_stories, new_urls), False)
        cls._data = (new_stories, new_urls)

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

if __name__ == '__main__':
    # Friendlist
    links = load_data(CFG_FRIENDS)
    is_friends_loaded = True
    if links is None:
        links = get_friend_links()
        is_friends_loaded = False

    # Stories
    stories = load_data(CFG_STORIES, False)
    if stories is None:
        stories = {}
    elif type(stories) == tuple:
        stories, _ = stories
    new_stories = {}
    new_urls = []
    # Load new stories and compare with saved ones
    for author_url, author_name in links:
        print "%s [%s]" % (author_name, author_url)
        author_stories = get_stories(author_url)
        new_stories[author_url] = author_stories
        if author_url not in stories:
            continue  # We just imported new author
        for url, story in author_stories.iteritems():
            if (url not in stories[author_url] or
                    stories[author_url][url] != story):
                print_story(url, *story)
                new_urls.append(url)

    # Store loaded data
    if not is_friends_loaded:
        store_data(CFG_FRIENDS, links)
    store_data(CFG_STORIES, (new_stories, new_urls), False)
