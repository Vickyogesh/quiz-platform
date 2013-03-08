import ConfigParser
import os.path


class Settings(object):
    """
    Web service settings.
    The following settings is provided:
        session - dict with session config
        cache - dict with cache config
        dbinfo - dict with database config
    """

    CONFIG_FILE = 'config.ini'

    def __init__(self, config_paths, verbose=True):
        """ Create settings using file_path source. """

        self.root, cfg_file = self._get_config_file_info(config_paths)
        self.defaults = {'here': self.root}
        if verbose:
            print('Using configuration ' + cfg_file)
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(cfg_file)
        self._parse_session_and_cache(cfg)
        self._parse_db(cfg)
        self._parse_testing(cfg)

    # Return root directory and file path of the configuration
    def _get_config_file_info(self, paths):
        for path in paths:
            f = os.path.join(path, Settings.CONFIG_FILE)
            if os.path.exists(f):
                path = os.path.abspath(path)
                path = os.path.normcase(path)
                return (path, f)
        raise Exception("Can't find configuration in " + str(paths))

    def _fill_params(self, cfg, dest, section, prefix=''):
        for name, val in cfg.items(section, vars=self.defaults):
            dest[prefix + name] = os.path.expandvars(val)

    # Put session info to the self.session
    # and cache info to the self.cache
    # TODO: cache
    def _parse_session_and_cache(self, cfg):
        self.session = {}
        self.cache = {}
        self._fill_params(cfg, self.session, 'session', 'session.')

    # Parse db info and put into self.dbinfo
    # self.dbinfo['database'] will contain full path to the database
    def _parse_db(self, cfg):
        self.dbinfo = {}
        self._fill_params(cfg, self.dbinfo, 'database')

        # Construct database path
        if self.dbinfo['uri'][-1] == '/':
            self.dbinfo['database'] = self.dbinfo['uri'] + self.dbinfo['dbname']
        else:
            self.dbinfo['database'] = self.dbinfo['uri'] + '/' + self.dbinfo['dbname']

        try:
            params = self.dbinfo['params']
            self.dbinfo['database'] += '?' + params
        except KeyError:
            pass

    # Parse testing section
    def _parse_testing(self, cfg):
        self.testing = {}
        try:
            self._fill_params(cfg, self.testing, 'testing')
        except Exception:
            pass
