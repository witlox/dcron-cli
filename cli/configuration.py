#!/usr/bin/env python
# -*- coding: utf-8 -*-#

# MIT License
#
# Copyright (c) 2019 Pim Witlox
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import logging
from json import JSONEncoder, JSONDecoder

from pathlib import Path
from os.path import exists, dirname, expandvars, expanduser


class Site(object):
    """
    Default representation of a site
    """
    name = 'default'
    servers = ['localhost']
    port = 8080
    ssl = False
    log_level = 'info'
    username = None
    password = None


class Configuration(object):

    logger = logging.getLogger(__name__)

    def __init__(self, config_file=None, create=True):
        self.sites = [Site()]
        if create and config_file:
            self.write(expandvars(expanduser(config_file)))
        if config_file and exists(expandvars(expanduser(config_file))):
            self.read(expandvars(expanduser(config_file)))

    def read(self, path):
        if not exists(path):
            self.logger.error("could not locate config at {0}".format(path))
        with open(path, 'r') as handle:
            self.sites = json.loads(handle.readline(), cls=SiteDecoder)

    def write(self, path):
        if not exists(path):
            self.logger.debug("writing new config to {0}".format(path))
            if not exists(dirname(path)):
                Path.mkdir(Path(dirname(path)), parents=True)
            with open(path, 'w') as cf:
                cf.write(json.dumps(self.sites, cls=SiteEncoder))
        else:
            self.logger.debug("already found config at {0}, overwriting it".format(path))
            with open(path, 'w') as cf:
                cf.write(json.dumps(self.sites, cls=SiteEncoder))


class SiteEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, Site):
            return {
                '_type': 'site',
                'name': o.name,
                'servers': json.dumps(o.servers),
                'port': o.port,
                'ssl': o.ssl,
                'log_level': o.log_level,
                'username': '' if not o.username else o.username,
                'password': '' if not o.password else o.password,
            }
        return JSONEncoder.default(self, o)


class SiteDecoder(JSONDecoder):

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(obj):
        if '_type' not in obj:
            return obj
        if obj['_type'] == 'site':
            site = Site()
            site.name = obj['name']
            site.servers = json.loads(obj['servers'])
            site.port = obj['port']
            site.ssl = obj['ssl']
            site.log_level = obj['log_level']
            if obj['username'] != '':
                site.username = obj['username']
            if obj['password'] != '':
                site.password = obj['password']
            return site
        return obj
