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

    def __str__(self, separator=':'):
        return '%s%s%s' % (self.server, separator, self.name or '')


class Table(object):
    def __init__(self, schema, name):
        self.schema = schema
        self.name = name

    def __str__(self, separator=':'):
        return '%s%s%s' % (self.schema.__str__(separator), separator, self.name)


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


def dump_servers(servers, outfile, separator=':'):
    for server in servers:
        print(server.__str__(), file=outfile)
        for schema in server.schemas():
            print(schema.__str__(separator), file=outfile)
            for table in schema.tables():
                print(table.__str__(separator), file=outfile)


def main():
    def fp(filename):
        if filename == '-':
            return sys.stdout
        if os.path.exists(filename):
            raise argparse.ArgumentTypeError("File already exists.")
        return open(filename, 'w')

    def dump(args):
        servers = get_config(args.config)
        dump_servers(servers, args.output, args.separator)

    # if user config exists, use it by default
    confpath = os.path.join(
        os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config')),
        'greptable.conf')
    if not os.path.exists(confpath):
        confpath = 'greptable.conf'

    parser = argparse.ArgumentParser(description="List tables of SQL databases for easy schema greps")
    parser.add_argument('-s', '--separator', default=':')
    parser.add_argument('-c', '--config', default=confpath)
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    dump_parser = subparsers.add_parser('dump', help="Dump the table list")
    dump_parser.add_argument('-o', '--output', default='-', type=fp)
    dump_parser.set_defaults(method=dump)

    args = parser.parse_args()
    return args.method(args)


if __name__ == '__main__':
    main()
