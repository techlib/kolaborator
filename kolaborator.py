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
        """Further process the notification, get all the details and find the perpetrator"""
        notice = self.db.infringements.get(item_id)
        internal_ip = search_flow(notice.ip_address, notice.port, notice.source_timestamp)
        eduroam, staff, user = search_radius(internal_ip, notice.source_timestamp)
        if eduroam:
            # send notification to users eduroam institution
        else:
            # write row into table and if more than 3 do something, else notify the user of inapropriate activity


    def search_flow(self, external_ip, port, timestamp):
        """Look into netflow for internal ip address of the perpetrator"""

        query = 'select * \
                    from(\
                        select \
                            (flow.fields ->> \'sourceIPv4Address\'::text)::inet AS internal_addr,\
                            flow."time" - (flow.uptime - ((flow.fields ->> \'flowStartSysUpTime\'::text)::double precision)) * \'00:00:00.001\'::interval AS start_time, \
                            flow."time" - (flow.uptime - ((flow.fields ->> \'flowEndSysUpTime\'::text)::double precision)) * \'00:00:00.001\'::interval AS stop_time \
                        from flow \
                        where flow.fields @> \'{{"postNATSourceIPv4Address": "{1}" , "postNAPTSourceTransportPort": {2} }}\'::jsonb) AS times\
                    where date_trunc(\'second\', times.start_time) <= \'{0}\' AND date_trunc(\'second\',times.stop_time + interval \'1 second\') >= \'{0}\'\
                    '.format(timestamp, external_ip, port)

        res = []

        for row in self.db_flow.execute(query).fetchall():
            res.append(dict(zip(row.keys(), row.values())))

        return res[0]['internal_addr']

    def search_radius(self, internal_ip, timestamp):
        """Find the user,to whom was the internal ip address leased"""
        # look into radius if it is eduroam user, reader or employee
        query = 'select \
                    username, \
                    realm, \
                    user, \
                    description \
                from accounting \
                where framed_ip = \'{0}\' and start_time <= \'{1}\' and update_time >= \'{1}\' \
                    '.format(internal_ip, timestamp)

        res = []

        for row in db_radius.execute(query).fetchall():
            res.append(dict(zip(row.keys(), row.values())))

        if res[0]['user'] == None:
            staff = False
            user = res[0]['username']
            if res[0]['realm'] = 'NULL':
                eduroam = False
            else:
                eduroam = True
        else:
            staff = True
            eduroam = False
            user = res[0]['user']

        return eduroam, staff, user

    def send_message(self):
        """Send warning to the user / eduroam institution"""
        return

    def send_response(self):
        """Reply to complainant"""
        return
# vim:set sw=4 ts=4 et:
