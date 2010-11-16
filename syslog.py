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


#
# SyslogBot is heavily inspired by:
#
# pySysBot -- http://gitorious.org/pysysbot
# System status bot -- http://www.uhoreg.ca/programming/jabber/systembot
#
# SyslogBot includes many features of the above, but his main feature is to
# deliver syslog messages over jabber/xmpp to a list of users.

#
# Requires: python-jabberbot > 0.10 !
#

try:
    from jabberbot import JabberBot, botcmd

    import logging

    import time 
    import datetime
    import os
    import statgrab

except ImportError:
    print """Cannot find all required libraries please install them and try again"""
    raise SystemExit

class SyslogBot(JabberBot):
    """This is a syslog (named pipes) to jabber bot. """

    def __init__( self, jid, password, pipe, statusReport = False, res = None):
        super( SyslogBot, self).__init__( jid, password, res)
        self._pipe = pipe
	self._status = statusReport

# Bot Commands from pySysBot

    @botcmd
    def who(self, mess, args):
        """Display who's currently logged in"""
        who = os.popen('/usr/bin/who').read().strip()
        return who

    @botcmd
    def uptime(self, mess, args):
        """Displays the server uptime"""
        uptime = open('/proc/uptime').read().split()[0]
        # This is heavily based on the work of Hubert Chathi and his System status bot.
        uptime = float(uptime)
        (uptime,secs) = (int(uptime / 60), uptime % 60)
        (uptime,mins) = divmod(uptime,60)
        (days,hours) = divmod(uptime,24)
        uptime = 'Uptime: %d day%s, %d hour%s %02d min%s' % (days, days != 1 and 's' or '', hours, hours != 1 and 's' or '', mins, mins != 1 and 's' or '')
        return uptime

    @botcmd
    def load(self, mess, args):
        """Displays the server load over the last 1, 5, and 15 minutes"""
        loaddata = []
        load = os.getloadavg()
        for i in load:
                loaddata.append(i)
        load_data = "Load average of the system" + \
                "\n" +"  1 min: \t" + str(loaddata[0]) + \
                "\n" +"  5 min: \t" + str(loaddata[1]) + \
                "\n" +" 15 min: \t" + str(loaddata[2])
        return load_data

    @botcmd
    def processes(self, mess, args):
        """Displays the processes of the server"""
        process = statgrab.sg_get_process_count()
        load_process = "Processes" + \
                "\n" + " Zombie: \t"    + str(process['zombie'])  + \
                "\n" + " Running: \t"   + str(process['running'])  + \
                "\n" + " Stopped: \t"   + str(process['stopped'])  + \
                "\n" + " Sleeping: \t"  + str(process['sleeping']) + \
                "\n" + " Total: \t\t"   + str(process['total'])
        return load_process

    @botcmd
    def ip(self, mess, args):
        """Displays the IP Addresses of the server"""
        #Source: http://commandline.org.uk/python/how-to-find-out-ip-address-in-python/
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.com', 0))
        int_ipaddr = s.getsockname()[0]
        ext_ipaddr = urllib2.urlopen("http://whatismyip.com/automation/n09230945.asp").read()
        data_ipaddr = "Internal IP address: \t" + int_ipaddr + \
               "\n" +"External IP address: \t" + ext_ipaddr
        return data_ipaddr

# Own Bot commands
    @botcmd
    def mem(self, mess, args):
        """Displays the memory status of the server"""
	memory, swap = self._mem()
	memStr = ["Memory usage:"]
	memStr.append( "Memory:\t %i %%  (%i MB/ %i MB)" % (memory[3], memory[1], memory[0]))
	memStr.append( "Swap:\t %i %%  (%i MB/ %i MB)" % (swap[3], swap[1], swap[0]))
        return '\n'.join(memStr)

# Helpers

    def _mem(self):
        """Calculates the memory status of the server"""
        swapstat = statgrab.sg_get_swap_stats()
        memstat = statgrab.sg_get_mem_stats()
        #Some calculation to get the perc of the data
        memdiff = memstat['total'] - memstat['free']
        memfloat = float (memdiff) / float(memstat['total'])
        memperc = int(round (memfloat * 100))
        swapdiff = swapstat['total'] - swapstat['free']
        swapfloat = float (swapdiff) / float(swapstat['total'])
        swapperc = int(round (swapfloat * 100))
        return ((memstat['total']/1048576 , \
                 memstat['used']/1048576 , \
                 memstat['free']/1048576 , \
                 memperc), \
                (swapstat['total']/1048576 , \
                 swapstat['used']/1048576 , \
                 swapstat['free']/1048576 , \
                 swapperc))

# IDLE Command(s)

    def idle_proc( self ):
        self._idle_syslog()
	if self._status:
	   self._idle_status()
	self._idle_show()

    def _idle_syslog( self ):
        readline = self._pipe.readline
        line = readline()
        msgs = []
        while line:
            msgs.append( line.strip() )
            line = readline()
        for msg in msgs:
            self.broadcast(msg)

    def _idle_status( self ):
        status = []

        load = 'load average: %s %s %s' % os.getloadavg()
        status.append(load)

        # calculate the uptime
        status.append(self.uptime(None, None))

        # calculate memory and swap usage
	memory, swap = self._mem()
	status.append( "Memory:\t %i %%" % memory[3])
	status.append( "Swap:\t %i %%" % swap[3])

        status = '\n'.join(status)
        # TODO: set "show" based on load? e.g. > 1 means "away"
        if self.status_message != status:
            self.status_message = status
	
    def _idle_show( self ):
        load = os.getloadavg()
        if load[0] < 1:
            self.status_type = self.AVAILABLE
	elif load[0] < 2:
            self.status_type = self.AWAY
        else:
            self.status_type = self.XA
	
# Fill in the JID + Password of your JabberBot here...
(JID, PASSWORD) = ('syslogbot@ebutterfly.de','FlfybtObg')

# Activating Debug
logging.basicConfig(level=logging.DEBUG)

slBot = SyslogBot( JID, PASSWORD, open("syslogPipe"))

slBot.serve_forever()

