#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import argparse
import io
import os
import sys

from sqlalchemy import create_engine, inspect

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class Server(object):
    def __init__(self, url, name=None):
        if name is None:
            name = urlsplit(url).hostname
        if name is None:
            name = url
        self.url = url
        self.name = name
        self.engine = create_engine(self.url)

    def __str__(self):
        return self.name

    def schemas(self):
        inspector = inspect(self.engine)
        dbs = inspector.get_schema_names()
        if not len(dbs):
            yield Schema(self, inspector.default_schema_name)
        for dbname in dbs:
            yield Schema(self, dbname)


class Schema(object):
    def __init__(self, server, name):
        self.server = server
        self.name = name

    def tables(self):
        inspector = inspect(self.server.engine)
        for tablename in inspector.get_table_names(self.name):
            yield Table(self, tablename)

    def __str__(self):
        return '%s:%s' % (self.server, self.name or '')


class Table(object):
    def __init__(self, schema, name):
        self.schema = schema
        self.name = name

    def __str__(self):
        return '%s:%s' % (self.schema, self.name)


def get_config(path):
    with io.open(path, encoding='utf-8') as f:
        config = f.read()
    return parse_config(config)


def parse_config(config_text):
    config = configparser.RawConfigParser()
    if hasattr(config, 'read_file'):
        config.read_file(io.StringIO(config_text))
    else:
        config.readfp(io.StringIO(config_text))
    for url in config.sections():
        items = dict(config.items(url))
        yield Server(url, items.get('name'))


def print_servers(servers, outfile):
    for server in servers:
        print(server, file=outfile)
        for schema in server.schemas():
            print(schema, file=outfile)
            for table in schema.tables():
                print(table, file=outfile)


def main():
    def fp(filename):
        if filename == '-':
            return sys.stdout
        if os.path.exists(filename):
            raise argparse.ArgumentTypeError("File already exists.")
        return open(filename, 'w')

    parser = argparse.ArgumentParser(
        description='')
    parser.add_argument('-c', '--config', default='greptable.conf')
    parser.add_argument('-o', '--output', default='-', type=fp)
    args = parser.parse_args()

    servers = get_config(args.config)
    print_servers(servers, outfile=args.output)


if __name__ == '__main__':
    main()
