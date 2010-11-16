#!/usr/bin/python

# SyslogBot: A simple Syslog to jabber/xmpp bot
#            based on the JabberBot framework
# Copyright (c) 2010 Michael Trunner <michael@trunner.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from jabberbot import JabberBot, botcmd

import threading
import time 
import select

# Fill in the JID + Password of your JabberBot here...
(JID, PASSWORD) = ('syslogbot@ebutterfly.de','FlfybtObg')

class SyslogBot(JabberBot):
    """This is a syslog (named pipes) to jabber bot. """

    def __init__( self, jid, password, pipe, res = None):
        super( SyslogBot, self).__init__( jid, password, res)
	self._pipe = pipe

    def idle_proc( self):
	readline = self._pipe.readline
	line = readline()
	msgs = []
	while line:
		msgs.append( line.strip() )
		line = readline()
	for msg in msgs:
		self.broadcast(msg)
	
	
# Activating Debug
import logging
logging.basicConfig(level=logging.DEBUG)

slBot = SyslogBot( JID, PASSWORD, open("syslogPipe"))

slBot.serve_forever()

