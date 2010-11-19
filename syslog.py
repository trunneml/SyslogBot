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
    # These imports are only for the startup
    import logging
    import ConfigParser
    import optparse

    # These imports are only for the Bot class
    from jabberbot import JabberBot, botcmd

    import datetime
    import os
    import statgrab
    import socket
    import urllib2

    import threading
    import time 
    import select

except ImportError:
    print """Cannot find all required libraries please install them and try again"""
    raise SystemExit

class SyslogBot(JabberBot):
    """This is a syslog (named pipes) to jabber bot. """

    def __init__( self, jid, password, pipes, statusReport = False, res = None):
        super( SyslogBot, self).__init__( jid, password, res)
        self._pipes = dict(pipes)
	self._status = statusReport
        self.thread_killed = False
        self._th = threading.Thread( target = self.thread_proc)
        self._th.start()

    def shutdown(self):
	self.thread_killed = True

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
	self.log.debug("Running idle proc")
	if self._status:
	   self._idle_status()
	self._idle_show()

    def _idle_status( self ):
        """ Display system informations in the status message"""
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
        if self.status_message != status:
            self.status_message = status
	
    def _idle_show( self ):
        """ Display load as xmpp status """
        load = os.getloadavg()
        if load[0] < 1:
            self.status_type = self.AVAILABLE
	elif load[0] < 2:
            self.status_type = self.AWAY
        else:
            self.status_type = self.XA

# Thread functions
    def thread_proc(self):
        pipe2jids = self._pipes
        pipes = pipe2jids.keys()
        while not self.thread_killed:
            self.log.debug("Looking for next line on pipe")
            rList = select.select(pipes,[],[],0.5)[0]
            for pipe in rList:
                msg = pipe.readline()
                msg = msg.strip()
                # Sometimes named pipes generating empty lines :-?
                if msg:
                    jids = pipe2jids[pipe]
                    if jids:
                        for jid in jids:
                            self.log.debug("Sending \"%s\" to %s" % (msg, jid))
                            self.send(jid, msg)
                    else:
                        self.log.debug("Broadcasting \"%s\" to all online users" % msg)
                        self.broadcast(msg)
                else:
                    # When the pipe gives us empty lines normally
                    # this means select.select doesn't work. (No idea why)
                    # To reduce resource consuming we sleep one second
                    time.sleep(1)

def main():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", action="store", type="string", dest="configFile", help="Read configuration from FILE", metavar="FILE", default="/etc/syslogBot.cfg")
    parser.add_option("-d", "--debug", dest="debug", action="store_true", help="Activate debug mode")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true", help="Activate quiet mode")
    (options, args) = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif options.quiet:
        logging.basicConfig(level=logging.WARNING)
    logging.basicConfig(level=logging.INFO)

    config = ConfigParser.SafeConfigParser()
    logging.info("Reading config from %s" % options.configFile)
    config.read(options.configFile)
    jid = config.get("JabberLogin", "JID")
    pwd = config.get("JabberLogin", "Password")
    
    # Reading all Pipe setups
    pipes = []
    for pipe in filter ( lambda x: x <> "JabberLogin", config.sections()):
        logJIDs = config.get(pipe, "JIDs")
        if logJIDs == "":
            logJIDs = None
        else:
            logJIDs = map(lambda x: x.strip(), logJIDs.split(","))
        logPipe = config.get("Syslog", "Pipe")
        logging.info("Waiting until named pipe (%s) is ready ..." % logPipe)
        logPipe = open(logPipe)
        pipes.append((logPipe, logJIDs))

    logging.info("Starting Syslog Bot ...")
    slBot = SyslogBot( jid, pwd, pipes )
    slBot.serve_forever()

if __name__ == '__main__':	
    main()
