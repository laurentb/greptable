#!/usr/bin/env python
from __future__ import print_function, unicode_literals

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

from sqlalchemy import create_engine, inspect


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

    def databases(self):
        inspector = inspect(self.engine)
        for dbname in inspector.get_schema_names():
            yield Database(self, dbname)


class Database(object):
    def __init__(self, server, name):
        self.server = server
        self.name = name

    def tables(self):
        inspector = inspect(self.server.engine)
        for tablename in inspector.get_table_names(self.name):
            yield Table(self, tablename)

    def __str__(self):
        return '%s:%s' % (self.server, self.name)


class Table(object):
    def __init__(self, database, name):
        self.database = database
        self.name = name

    def __str__(self):
        return '%s:%s' % (self.database, self.name)


def get_config(path='greptable.conf'):
    with open(path) as f:
        config = f.read()
    for url in config.splitlines():
        yield Server(url)


if __name__ == '__main__':
    servers = get_config()
    for server in servers:
        print(server)
        for database in server.databases():
            print(database)
            for table in database.tables():
                print(table)
