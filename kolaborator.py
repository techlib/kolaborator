#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

__all__ = ['Kolaborator']

from os import system
from twisted.python import log
from twisted.internet import task
from json import dump, load


class Kolaborator(object):
    def __init__(self, db, db_flow, db_radius):
        self.db = db
        self.db_flow = db_flow
        self.db_radius = db_radius

    def notify(self, event):
        """Process a database notification."""
        if event.channel == 'kolaborator':
            [table_name, item_id] = event.payload.split(',id,')
        process(item_id)

    def process(self, item_id):
        notice = self.db.infringements.get(item_id)
        internal_ip = find_flow(notice.ip_address, notice.port, notice.source_timestamp)

    def find_flow(self, external_ip, port, timestamp):
        
        return internal_ip

    def find_radius(self, internal_ip, timestamp):

        return eduroam, user_id

    def send_message(self):
        return

    def send_response(self):
        return
# vim:set sw=4 ts=4 et:
