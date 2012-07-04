from tornado import auth, web
from tornado import database
from tornado.options import options

import xmltodict
# import hashlib
# import base64
# from random import randint
# from datetime import *
import re

import db
from helper import *


def connection():
    """
    Returns DB connection.

    """
    return database.Connection(
        host        = options.mysql_host,
        database    = options.mysql_database,
        user        = options.mysql_user,
        password    = options.mysql_password,
    )


class Import(myRequestHandler):
    """

    """

    def get(self):
        filelisting = "/Users/michelek/amphora-xmls.lst"
        fl_handler = open(filelisting)
        all_docs = {}
        cell_names = {}
        cell_names["Dokumendid"] = {}
        cell_names['Sonumid'] = {}

        # ^[\s]*   - any whitespace following beginning of line
        # [\w]     - match only, if group is followed by alphanumeric
        # r"foo\"   - treat "foo\" as a raw string
        newline_pattern = re.compile(r"^[\s]*([\w])", re.MULTILINE)
        newline = '|newline|'
        newline_replacement = newline + '\\1'

        sql_a = []

        db = connection()

        for fname in fl_handler.readlines():
            fname = fname.strip()
            fh = open(fname, "r")
            file_contents = newline_pattern.sub(newline_replacement, fh.read())
            exported_data = xmltodict.parse(file_contents)['ExportedData']
            fh.close()

            for doc_type in exported_data.keys():
                sql_a = []
                for cn in exported_data[doc_type].keys():

                    cell_names[doc_type][cn] = 1
                    node = exported_data[doc_type][cn]

                    if not node:
                        continue
                    if not '#text' in node:
                        continue
                    if node['#text'] == '':
                        continue

                    contents = node['#text'].replace('\\', r"\\").replace("'", r"\'").replace("%","%%").replace(newline,"\n")

                    sql_set = u'%s = \'%s\'' % (cn, contents)
                    sql_a.append(sql_set)

                if len(sql_a) == 0:
                    continue

                sql = u'INSERT INTO x_amphora_%s SET %s;' % (doc_type, ', '.join(sql_a))
                try:
                    db.execute(sql)
                except Exception, e:
                    logging.debug(sql)
                    logging.debug(e)


handlers = [
    ('/amphora/import', Import),
]
