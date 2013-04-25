from __future__ import print_function
import argparse
import tempfile
import os
import os.path
import subprocess
import sys
from texttable import Texttable
from time import time

# Server data
hosts = {
    'production': {
        'uid': '511e20435973cae491000014',
        'domain': 'quizplatform-editricetoni.rhcloud.com'
    },
    'test': {
        'uid': '511d27934382ec2a38000025',
        'domain': 'quizplatformtest-editricetoni.rhcloud.com'
    }
}


def get_remote_command(server, cmd):
    info = hosts[server]
    return 'ssh -t {0}@{1} {2}'.format(info['uid'], info['domain'], cmd)


def check_remote_logs(server):
    print('Checking logs snapshot...')
    info = hosts[server]
    base = '/var/lib/openshift/{0}'.format(info['uid'], info['domain'])
    fmt = 'bash {0}/app-root/runtime/repo/misc/lrotate.sh -checkarch'

    cmd = get_remote_command(args.server, fmt.format(base))
    res = subprocess.call(cmd.split(' '))

    if res != 0:
        sys.exit(res)
    print('Checking logs snapshot... done')


# Construct path to the remote log file.
def get_log_remote_path(server, log='app.log'):
    info = hosts[server]
    fmt = '{0}@{1}:/var/lib/openshift/{0}/diy-0.1/logs/{2}'
    return fmt.format(info['uid'], info['domain'], log)


# Construct path to the local log file.
def get_temp_path(log='app.log'):
    path = tempfile.gettempdir()
    temp = "%s-%.7f.tmp" % (log, time())
    return os.path.join(path, temp)


# Convert local path to unix style path
# since we use unix scp tool.
def convert_to_unixstyle(path):
    path = path.replace('\\', '/')
    if path.find(':') != -1:
        path = path.replace(':', '')
        path = '/' + path
    return path


# Download remote log to the local log file
# and return local log file path.
def download_log(server, log='app.log', notemp=False):
    info = hosts[server]
    print("Downloading %s => %s" % (info['domain'], log))
    remote = get_log_remote_path(server, log)
    if notemp:
        local_file = log
    else:
        local_file = get_temp_path(log)
    res = subprocess.call(['scp', remote, convert_to_unixstyle(local_file)])

    if res != 0:
        sys.exit(res)

    return local_file


# TODO: maybe calc median?
# Analyze requests log.
# Print performance statistics for each unique request.
def analyze_perfornace(log_file, table_width):
    data = {}  # Statistics results storage.

    for line in file(log_file):
        process_log_line(line, data)

    print_stat(data, table_width)


# Create results storage if needed and return it.
def get_data(dest, url, method):
    key = method + url
    if key not in dest:
        dest[key] = {
            'url': url,
            'min': 0,
            'max': 0,
            'avg': 0,
            'count': 0,
            'total': 0,
            'method': method,
            'bad': set()
        }
    return dest[key]


def process_log_line(line, data):
    if not line.startswith('[pid:'):
        return
    lst = line.split(' ')
    method = lst[16]
    url = lst[17]
    msec = int(lst[23])

    if not url.startswith('/v1'):
        return

    if '?' in url:
        url = url[:url.find('?') - 1]
    if url.startswith('/v1/quiz/'):
        url = '/v1/quiz'
    elif url.startswith('/v1/exam/'):
        url = '/v1/exam'
    elif url.startswith('/v1/student/me/topicerrors/'):
        url = '/v1/student/me/topicerrors'

    info = get_data(data, url, method)

    if msec - info['min'] > 1000:
        if len(info['bad']) < 300:
            info['bad'].add(msec)
        return

    info['count'] += 1
    info['total'] += msec
    if info['min'] == 0 or info['min'] > msec:
        info['min'] = msec
    if info['max'] < msec:
        info['max'] = msec


def print_stat(data, table_width=100):
    rows = []
    for _, item in data.items():
        if len(item['bad']):
            s = sorted(item['bad'])
            bad = '%d - %d' % (s[0], s[-1])
        else:
            bad = ''
        rows.append([item['method'], item['url'],
                     item['total'] / item['count'], item['min'],
                     item['max'], item['count'], bad])

    rows.sort(key=lambda x: (x[0], x[4]), reverse=True)

    table = Texttable(table_width)
    table.set_deco(Texttable.HEADER)
    table.set_cols_align(["l", "l", "r", "r", "r", "r", "r"])
    table.header(["method", "URL", "avg", "min", "max", "count", 'bad'])
    table.add_rows(rows, header=False)
    print('\n', table.draw())


def do_analyze(args):
    if args.log:
        log_file = args.log
        args.noclean = True
    else:
        log_file = download_log(args.server)

    analyze_perfornace(log_file, args.w)

    if not args.noclean:
        os.remove(log_file)
    else:
        print('\nLog file: %s' % log_file)


def do_getlogs(args):
    check_remote_logs(args.server)
    download_log(args.server, 'logs-snapshot.tar.bz2', True)

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Quiz Service log tool.',
    epilog="""Examples:
    Analyse requests log from production server:
        logstat.py analyze

    Analyse requests log from test server and don't remove log file:
        logstat.py -s test analyze -n

    Analyse specified log:
        logstat.py analyze -l log.txt

    Download logs snapshot from the peduction server:
        logstat.py getlogs

    Download logs snapshot from the test server:
        logstat.py -s test getlogs
    """)

parser.add_argument('-s', '--server', choices=hosts.keys(),
                    default='production',
                    help='Source server (default: %(default)s).')
sp = parser.add_subparsers(title='Actions', help='Avaliable actions.')

# Logs analyzer arguments
p = sp.add_parser('analyze', help='Analyze logs (default uWSGI logs).')
p.add_argument('-n', '--noclean', action='store_true',
               help='Do not delete log.')
p.add_argument('-l', '--log',
               help='Specify log file to analyze.')
p.add_argument('-w', type=int, default=100,
               help='Max table width (default: %(default)s).')
p.set_defaults(func=do_analyze)

# Logs downloader arguments
p = sp.add_parser('getlogs', help='Download logs snapshot.')
p.set_defaults(func=do_getlogs)

args = parser.parse_args()
args.func(args)
