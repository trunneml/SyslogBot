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
# SyslogBot is inspired by:
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

except ImportError:
    print """Cannot find all required libraries please install them and try again"""
    raise SystemExit

class SyslogBot(JabberBot):
    """This is a syslog (named pipes) to jabber bot. """

    def __init__( self, jid, password, pipe, res = None):
        super( SyslogBot, self).__init__( jid, password, res)
        self._pipe = pipe

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
    def mem(self, mess, args):
        """Displays the memory status of the server"""
        swapstat = statgrab.sg_get_swap_stats()
        memstat = statgrab.sg_get_mem_stats()
        #Some calculation to get the perc of the data
        memdiff = memstat['total'] - memstat['free']
        memfloat = float (memdiff) / float(memstat['total'])
        memperc = int(round (memfloat * 100))
        swapdiff = swapstat['total'] - swapstat['free']
        swapfloat = float (swapdiff) / float(swapstat['total'])
        swapperc = int(round (swapfloat * 100))
        mem_process = "Memory status" + \
                "\n" + " Mem Total : \t" + str(memstat['total']/1048576) + \
                " MB \t \t Swap Total : \t" + str(swapstat['total']/1048576) + \
                " MB" + \
                "\n" + " Mem Used : \t" + str(memstat['used']/1048576) + \
                " MB \t \t Swap Used : \t" + str(swapstat['used']/1048576) + \
                " MB" + \
                "\n" + " Mem Free : \t" + str(memstat['free']/1048576)  + \
                " MB \t \t \t Swap Free : \t" + str(swapstat['free']/1048576) + \
                " MB" + "\n" + " Mem Used : \t" + str(memperc) + " %" + \
                " \t \t \t Swap Used : \t" + str(swapperc) + " %" 
        return mem_process

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

# IDLE Command(s)

    def idle_proc( self):
        readline = self._pipe.readline
        line = readline()
        msgs = []
        while line:
            msgs.append( line.strip() )
            line = readline()
        for msg in msgs:
            self.broadcast(msg)
	
	
# Fill in the JID + Password of your JabberBot here...
(JID, PASSWORD) = ('syslogbot@ebutterfly.de','FlfybtObg')

# Activating Debug
logging.basicConfig(level=logging.DEBUG)

slBot = SyslogBot( JID, PASSWORD, open("syslogPipe"))

slBot.serve_forever()

