#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.python import log

from simplejson import dump, load


__all__ = ['Manager']


class Manager:
    def __init__(self, db, db_flow, db_radius, notifier):
        self.db = db
        self.db_flow = db_flow
        self.db_radius = db_radius
        self.notifier = notifier

    def start(self):
        log.msg('Starting manager...')

        # Listen to database notifications.
        log.msg('Listening to incident notifications...')
        self.notifier.listen('kolaborator', self.on_incident)

        log.msg('Manager started.')

    def on_incident(self, info):
        """
        A new incident has been reported.
        """

        # Payload has the format of "{table_name},id,{pkey_value}".
        _table_name, incident_id = info.split(',id,')

        return self.process(incident_id)

    def process(self, incident_id):
        """
        Further process the notification and find the perpetrator.
        """

        notice = self.db.infringements.get(incident_id)
        internal_ip = self.search_flow(notice.ip_address, notice.port, notice.source_timestamp)

        if internal_ip is None:
            log.msg('''
                Internal IP address for {ip_address}:{port} not found.
            '''.strip().format(**notice.__dict__))
            return

        user, username, realm = self.search_radius(internal_ip, notice.source_timestamp)

        log.msg('Perpetrator: {user}@{realm} ({username})'.format(**locals()))

        if realm is not None:
            log.msg('TODO: Send notification to users eduroam institution...')
        else:
            log.msg('TODO: Send notification to the user (if possible)...')

        log.msg('TODO: Write resolution to the database...')

    def search_flow(self, external_ip, port, timestamp):
        """
        Look into netflow for internal ip address of the perpetrator.
        """

        row = self.db_flow.execute('''
            SELECT *
            FROM (
                SELECT (flow.fields->>'sourceIPv4Address'::text)::inet AS internal_addr,
                       flow."time" - (flow.uptime - ((flow.fields ->> 'flowStartSysUpTime'::text)::double precision)) * '00:00:00.001'::interval AS start_time,
                       flow."time" - (flow.uptime - ((flow.fields ->> 'flowEndSysUpTime'::text)::double precision)) * '00:00:00.001'::interval AS stop_time
                FROM flow
                WHERE flow.fields @> json_build_object('postNATSourceIPv4Address', :addr, 'postNAPTSourceTransportPort', :port)::jsonb
            ) AS times
            WHERE :ts <@ tstzrange(times.start_time - interval '1 second', times.stop_time + interval '1 second')
        ''', params={'addr': external_ip, 'port': port, 'ts': timestamp}).first()

        return row.internal_addr if row is not None else None

    def search_radius(self, internal_ip, timestamp):
        """
        Find the user to whom was the internal ip address leased.
        """

        row = self.db_radius.execute('''
            SELECT username, realm, user, description
            FROM accounting
            WHERE framed_ip = :addr AND
                  start_time <= :ts AND
                  update_time >= :ts
        ''', params={'addr': internal_ip, 'ts': timestamp}).first()

        if row is not None:
            return None, None, None

        realm = row.realm if row.realm != 'NULL' else None

        return row.user, row.username, realm


# vim:set sw=4 ts=4 et:
