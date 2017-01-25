#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from txpostgres import txpostgres
from twisted.internet import defer
from twisted.python import log


__all__ = ['Notifier']


class Notifier:
    def __init__(self, reactor, db):
        self.db = txpostgres.Connection(reactor=reactor)
        self.conn = self.db.connect(db)

    def listen(self, channel, callback):
        log.msg('Listen to {} database notifications...'.format(channel))

        def do_listen(_):
            self.db.runOperation('LISTEN {channel}'.format(channel=channel))

        def do_dispatch(notify):
            if notify.channel == channel:
                callback(notify.payload)

        self.conn.addCallback(do_listen)
        self.db.addNotifyObserver(do_dispatch)


# vim:set sw=4 ts=4 et:
