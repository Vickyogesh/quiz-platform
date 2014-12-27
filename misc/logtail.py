#!/usr/bin/env python
"""Tail logs via HTTP.

It acts almost like:
    tail -f logfile | nc host ...
but sends data to the specific HTTP endpoint.

Usage:
    logtail.py (-h | --help)
    logtail.py [--pid PIDFILE] stop
    logtail.py [-d] [-v] [-t TAG] [--pid PIDFILE] [--log LOGFILE]
               FILE HTTP_ENDPOINT

Options:
    -h, --help     Show this help message.
    -d             Run as daemon.
    -v             Verbose log.
    -t TAG         Tag to prepend to each log line.
    --pid PIDFILE  PID file path.
    --log LOGFILE  Daemon log file.

    FILE           Source file to send.
    HTTP_ENDPOINT  Destination HTTP endpoint.

Commands:
    stop           Stop daemon.

Example:
    logtail.py -t mytag /path/to/apache.log http://my.endpoint.com/get-this

This command sends apache log
    [mytag] <log line>
    to
    http://my.endpoint.com/get-this?tag=mytag

"""
import os
import sys
import time
import logging
import requests
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from daemon import runner
from docopt import docopt


class DaemonRunner(runner.DaemonRunner):
    """Extends runner.DaemonRunner class with possibility to set action."""
    def __init__(self, app, action=None):
        self.__action = action
        super(DaemonRunner, self).__init__(app)
        self.daemon_context.files_preserve = [app.loghandler.stream]
        self.daemon_context.stdout = app.loghandler.stream
        self.daemon_context.stderr = app.loghandler.stream

    def parse_args(self, argv=None):
        runner.DaemonRunner.parse_args(
            self, [sys.argv[0], argv or self.__action])


class DaemonApp(object):
    """Base daemon application class.

    It provides logging feature and default parameters for the DaemonRunner.

    Subclass put all actions to run() method.
    """
    stdin_path = '/dev/null'
    stdout_path = '/dev/null'
    stderr_path = '/dev/null'
    pidfile_path = '/var/run/logtail.pid'
    pidfile_timeout = 5

    # Max size in bytes for the App logger, see _setup_log().
    # 5MB by default.
    max_log_size = '5242880'

    @staticmethod
    def can_create_pid(pidfile):
        """Check if we can create PID file."""
        try:
            f = open(pidfile, 'w')
            f.close()
            os.remove(pidfile)
            state = True
        except Exception:
            state = False
        return state

    def __init__(self, logfile=None, pidfile=None, verbose=False):
        self.logfile = logfile
        if pidfile is not None:
            self.pidfile_path = os.path.abspath(pidfile)

        self._setup_log(verbose)

    # Setup logging to write to file or standard output.
    def _setup_log(self, verbose):
        self.logger = logging.getLogger('logtail')
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                                '%d.%m.%Y %H:%M:%S')
        if self.logfile:
            self.loghandler = RotatingFileHandler(
                self.logfile,
                maxBytes=self.max_log_size,
                backupCount=1)
        else:
            self.loghandler = StreamHandler()
        self.loghandler.setFormatter(fmt)
        self.logger.addHandler(self.loghandler)

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        self.logger.debug(*args, **kwargs)

    def run(self):
        raise NotImplemented


def follow(filename, read_delay=1.0, buf_size=4, tag=None):
    """Yields `buf_size` lines from the file or any lines after timeout
    (2 x read_delay).

    Acts almost like a tail -f.

    Based on: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/157035
    """
    trailing = True
    line_terminators = ('\r\n', '\n', '\r')

    with open(filename, 'r') as in_file:
        in_file.seek(0, 2)  # seek end
        buf = []
        wait_count = 0
        while 1:
            where = in_file.tell()
            line = in_file.readline()
            if line:
                # This is just the line terminator added to the end of
                # the file before a new line, ignore.
                if trailing and line in line_terminators:
                    trailing = False
                    continue

                trailing = False
                if tag is not None:
                    line = '[{0}] {1}'.format(tag, line)
                buf.append(line)

                if len(buf) >= buf_size:
                    lines = ''.join(buf)
                    del buf[:]
                    yield lines
            else:
                wait_count += 1
                trailing = True
                in_file.seek(where)
                time.sleep(read_delay)
                if wait_count > 1 and buf:
                    wait_count = 0
                    lines = ''.join(buf)
                    del buf[:]
                    yield lines


class App(DaemonApp):
    # How many seconds wait before log reopen tyr if there was IO errors.
    log_wait_timeout = 2

    def __init__(self, logfile=None, pidfile=None, verbose=False,
                 source_log=None, http_endpoint=None, tag=None):
        super(App, self).__init__(logfile, pidfile, verbose)
        self.source_log = os.path.abspath(source_log) if source_log else None
        self.http_endpoint = http_endpoint
        self.tag = tag

    @staticmethod
    def create(docopt_args):
        """Construct application using docopt args."""
        return App(logfile=docopt_args['--log'],
                   pidfile=docopt_args['--pid'],
                   verbose=docopt_args['-v'],
                   source_log=docopt_args['FILE'],
                   http_endpoint=docopt_args['HTTP_ENDPOINT'],
                   tag=docopt_args['-t'])

    def do_follow(self):
        params = {'tag': self.tag} if self.tag is not None else None
        for data in follow(self.source_log, tag=self.tag):
            requests.post(self.http_endpoint, params=params, data=data)
            self.debug('Send %s bytes.', len(data))

    def run(self):
        self.info('(%s) %s -> %s', self.tag, self.source_log,
                  self.http_endpoint)
        while 1:
            try:
                self.do_follow()
            except IOError as e:
                self.info('%s', e)
                time.sleep(self.log_wait_timeout)
                continue
            else:
                break


if __name__ == '__main__':
    args = docopt(__doc__)
    app = App.create(args)
    cmd = 'stop' if args['stop'] else 'start'

    if args['-d'] or cmd == 'stop':
        if cmd != 'stop' and not App.can_create_pid(app.pidfile_path):
            print("Can't create PID file %s" % app.pidfile_path)
            sys.exit(1)
        runner = DaemonRunner(app, cmd)
        runner.do_action()
    else:
        try:
            app.run()
        except KeyboardInterrupt:
            pass
