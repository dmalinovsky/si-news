#!/usr/bin/python
# coding=utf-8
"""
Requirements: python-pyquery, python-qt4

friends.cfg format:
    ((author_url, author_name), ...)
stories.cfg format:
    ({author_url: {story_url: (title, size, desc), ...}, ...}, [new_url1, ...])
"""

import ConfigParser
import cPickle as pickle
import json
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtNetwork
from PyQt4 import QtWebKit
from pyquery import PyQuery as pq
import sys
import urllib2


# Folder to store all configuration
HOMEDIR = os.path.expanduser(os.path.join('~', '.si_news'))
if not os.path.isdir(HOMEDIR):
    os.mkdir(HOMEDIR)

# Index page for author stories
STORY_INDEX = 'indexdate.shtml'
# File name with list of friends
CFG_FRIENDS = os.path.join(HOMEDIR, 'friends.cfg')
# File name with list of stories
CFG_STORIES = os.path.join(HOMEDIR, 'stories.cfg')
# Various GUI settings, currently stores friends page URL only
CFG_GUI = os.path.join(HOMEDIR, 'si.ini')


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


class MainWindow(QtGui.QMainWindow):
    UPDATE_DELAY = 1000  # Delay in ms. between updates

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Friend pages data
        self.links = []
        # Author stories
        self.stories = {}
        # URLs with updated stories
        self.new_urls = []

        # Used to block run of second update while first one is running
        self.is_update_running = False

        self.setWindowTitle(u'Новинки СИ')
        self.setWindowIcon(QtGui.QIcon.fromTheme('face-cool'))
        self.content = QtWebKit.QWebView()
        self.init_content()

        self.content.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateExternalLinks)
        self.content.linkClicked.connect(self.on_link_clicked)
        self.content.page().linkHovered.connect(self.on_link_hovered)
        self.setCentralWidget(self.content)

        self.statusBar()

        # Menu
        options = QtGui.QAction(u'П&араметры', self)
        options.setShortcut(QtGui.QKeySequence('Ctrl+P'))
        options.setStatusTip(u'Настроить параметры программы')
        options.setIcon(QtGui.QIcon.fromTheme('document-properties'))
        options.triggered.connect(self.show_options)

        quit = QtGui.QAction(u'&Выход', self)
        quit.setShortcuts(QtGui.QKeySequence.Quit)
        quit.setStatusTip(u'Выход из программы')
        quit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        quit.triggered.connect(self.close)

        file_menu = self.menuBar().addMenu(u'&Файл')
        file_menu.addAction(options)
        file_menu.addSeparator()
        file_menu.addAction(quit)

        reload = QtGui.QAction(u'&Обновить', self)
        reload.setShortcuts(QtGui.QKeySequence.Refresh)
        reload.setStatusTip(u'Обновить список последних произведений')
        reload.setIcon(QtGui.QIcon.fromTheme('view-refresh'))
        reload.triggered.connect(self.update_content)

        view_menu = self.menuBar().addMenu(u'&Просмотр')
        view_menu.addAction(reload)

    def on_link_clicked(self, url):
        QtGui.QDesktopServices.openUrl(url)

    def on_link_hovered(self, link, title, content):
        if link:
            self.statusBar().showMessage(link)
        else:
            self.statusBar().clearMessage()

    def html_body_tag(self):
        """
        Returns HTML body opening tag with necessary styling.
        """
        return u'<body style="background-color:#e9e9e9;">'

    def init_content(self):
        # links=[(url, name), ...]
        self.links = Parser.get_friends()
        # stories={url: (title, size, desc), ...}
        self.stories, self.new_urls = Parser.get_stories()
        html = self.html_body_tag()
        for author_url, author_name in self.links:
            html += self.get_author_html(author_url, author_name)
        html += '</body>'

        self.content.setHtml(html)

    def get_author_html(self, author_url, author_name):
        """
        Returns HTML for updated author stories, if any.
        """
        html = ''
        if not author_url in self.stories:
            return html
        author_added = False
        for page_url, data in self.stories[author_url].iteritems():
            if page_url not in self.new_urls:
                continue
            if not author_added:
                html += u'<h1><a href="%s">%s</a></h1>' % (author_url, author_name)
                html += u'<dl>'
            author_added = True
            title, size, desc = data
            if desc is None:
                desc = ''
            html += u'<dt><li><b><a href="%s">%s</a> (%s)</b></li></dt><dd\
            style="color:#555555;">%s</dd>' %\
                (page_url, title, size, desc)
        html += u'</dl>'
        return html

    def update_content(self):
        if self.is_update_running:
            print 'Update is running already'
            return
        self.is_update_running = True
        # We don't want to change original list
        self.updating_links = [l for l in self.links]
        self.content.setHtml(self.html_body_tag())
        self.new_urls = []
        self.schedule_update_author()

    def schedule_update_author(self):
        """
        Initiates author update process.  Runs next step if there's any.
        At the end cleans up.
        This method is designed to run continuosly.
        """
        if self.updating_links:
            if not hasattr(self, 'progress_bar'):
                self.progress_bar = QtGui.QProgressBar()
                self.progress_bar.setMaximum(len(self.updating_links))
                self.progress_bar.setMinimum(0)
                self.progress_bar.setValue(0)
                self.statusBar().addWidget(self.progress_bar)
            QtCore.QTimer.singleShot(self.UPDATE_DELAY,
                    self.update_author)
        else:
            self.is_update_running = False
            # Whether we really updated any story
            if hasattr(self, 'progress_bar'):
                self.statusBar().removeWidget(self.progress_bar)
                del self.progress_bar
                Parser.save_stories(self.stories, self.new_urls)

    def update_author(self):
        Parser.update_author(self.updating_links[0][0], self.on_author_update)

    def on_author_update(self, stories):
        author_url, author_name = self.updating_links.pop(0)
        if stories is False:
            self.statusBar().showMessage(u'Не удалось скачать %s' % author_url)
        else:
            if author_url in self.stories:
                for url, story in stories.iteritems():
                    if (url not in self.stories[author_url] or
                            self.stories[author_url][url] != story):
                        self.new_urls.append(url)
            self.stories[author_url] = stories
            html = (self.content.page().mainFrame().toHtml() +
                self.get_author_html(author_url, author_name))
            self.content.setHtml(html)
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.schedule_update_author()

    def show_options(self):
        # Read configuration file
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(CFG_GUI)
        try:
            friends_url = cfg.get('DEFAULT', 'friends_url')
        except ConfigParser.NoOptionError:
            friends_url = ''
        options = OptionsDialog(self, friends_url)
        if options.exec_() != options.Accepted:
            return

        # Update friends list
        friends_url = str(options.friends_page.text())
        cfg.set('DEFAULT', 'friends_url', friends_url)
        with open(CFG_GUI, 'w') as cfg_file:
            cfg.write(cfg_file)
        self.statusBar().showMessage(u'Загрузка нового списка друзей...')
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.links = Parser.get_friend_links(friends_url)
        QtGui.QApplication.restoreOverrideCursor()
        self.statusBar().clearMessage()


class OptionsDialog(QtGui.QDialog):
    def __init__(self, parent=None, friends_url=''):
        super(OptionsDialog, self).__init__(parent)

        self.setWindowTitle(u'Настройки')

        self.friends_page = QtGui.QLineEdit(self)
        self.friends_page.setText(friends_url)
        friends_page_label = QtGui.QLabel(u'Адрес страницы друзей СИ', self)
        friends_page_label.setBuddy(self.friends_page)

        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(friends_page_label)
        hlayout.addWidget(self.friends_page)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel)
        update_btn = QtGui.QPushButton(u'Обновить список друзей')
        buttons.addButton(update_btn, buttons.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addWidget(buttons)

        self.setLayout(layout)

app = QtGui.QApplication(sys.argv)
wnd = MainWindow()
wnd.show()
sys.exit(app.exec_())
