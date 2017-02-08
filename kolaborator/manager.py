#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.python import log

from ldap3 import Server, Connection, ALL

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from string import Template

__all__ = ['Manager']


class Manager:
    def __init__(self, db, db_flow, db_radius, config, notifier):
        self.db = db
        self.db_flow = db_flow
        self.db_radius = db_radius
        self.notifier = notifier
        self.config = config

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
            db.processed.insert(
                infringement_id = incident_id,
                internal_ip = internal_ip,
                eduroam = true,
                eduroam_user = username
            )
        else:
            cn, email = self.search_ldap(username)
            self.notify_user(email, notice)
            db.processed.insert(
                infringement_id = incident_id,
                internal_ip = internal_ip,
                eduroam = false,
                cn = cn
            )
        notice.status = 'processed'
        db.commit()
        log.msg('Information inserted to db.')

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

        if row is None:
            return None, None, None

        realm = row.realm if row.realm != 'NULL' else None

        return row.user, row.username, realm

    def search_ldap(self, username):
        """
        Find user's email and CN on ldap
        """

        ldap_server = self.config.get('ldap', 'server')
        ldap_user = self.config.get('ldap', 'user')
        ldap_secret = self.config.get('ldap', 'secret')
        ldap_unit = self.config.get('ldap', 'unit')

        server = Server(ldap_server, get_info=ALL)
        conn = Connection(server, ldap_user, ldap_secret, auto_bind=True)
        conn.search(ldap_unit, '(&(objectclass=person)(uid=' + username + '))', attributes=['cn', 'mail'])
        entry = conn.entries[0]
        mail = entry.mail.values[0]
        cn = entry.cn.values[0]

        return cn, email

    def notify_user(self, to_addr, notice):
        """
        Notify user via email
        """

        smtp_host = self.config.get('email', 'url')
        smtp_port = self.config.get('email', 'port')
        smtp_user = self.config.get('email', 'user')
        smtp_passwd = self.config.get('email', 'password')

        from_addr = self.config.get('email', 'from')
        msg = MIMEMultipart()
        msg['Subject'] = "Some clever subject"
        msg['From'] = from_addr
        msg['To'] = to_addr

        message_template = open( '../email_templates/notify_user' )
        d = { 'filename':notice.filename, 'timestamp':notice.source_timestamp }

        text = Template( message_template.read() ).substitute(d)

        message_template.close()

        part = MIMEText(text, 'plain')
        msg.attach(part)

        smtp = smtplib.SMTP(smtp_host, smtp_port)
        smtp.starttls()
        smtp.login(smtp_user, smtp_passwd)

        smtp.sendmail(from_addr, to_addr, msg.as_string())
        smtp.quit()

        return

# vim:set sw=4 ts=4 et:
