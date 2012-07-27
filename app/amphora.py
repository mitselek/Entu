from tornado import auth, web
from tornado import database
from tornado.options import options

import xmltodict
import re

import db
from helper import *

import os
import datetime
def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


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

class LoadFiles(myRequestHandler):
    """

    """
    def get(self):
        self.db = connection()
        fileroot = "/Users/michelek/Downloads/KAExport/KAExport04062012/"

        sql = """
            SELECT entity_id, filename, local_file, property_definition_id
            FROM
            (   SELECT (SELECT id FROM entity WHERE gae_key = CONCAT('amphora_document_', md5(a.item_id)))             AS entity_id,
                       a.file_orig_name                                                                                AS filename,
                       (SELECT id FROM property_definition WHERE gae_key = 'amphora_document_file')                    AS property_definition_id,
                       concat('Dokumendid/', REPLACE(a.folder_path,'\\\\','/'), '/', a.item_id, '/', a.file_orig_guid) AS local_file
                FROM x_amphora_dokumendid a
                UNION
                SELECT (SELECT id FROM entity WHERE gae_key = CONCAT('amphora_message_', md5(a.item_id)))              AS entity_id,
                       a.file_orig_name                                                                                AS filename,
                       (SELECT id FROM property_definition WHERE gae_key = 'amphora_document_file')                    AS property_definition_id,
                       concat('Sonumid/', REPLACE(a.folder_path,'\\\\','/'), '/', a.item_id, '/', a.file_orig_guid)    AS local_file
                FROM x_amphora_sonumid a
            ) AS foo
            WHERE ifnull(filename, '') != '' AND filename != '.';
        """

        entity = db.Entity(user_locale=self.get_user_locale())

        for row in self.db.query(sql):
            # logging.debug(row)
            # logging.debug(row.entity_id)

            filename = fileroot + row.local_file
            try:
                fh = open(filename)
            except Exception, e:
                # logging.debug(e)
                continue

            logging.debug(filename)
            logging.debug(modification_date(filename))
            try:
                property_id = entity.set_property(entity_id=row.entity_id, relationship_id=None, property_definition_id=row.property_definition_id, value=None, property_id=None, uploaded_file={'filename':row.filename, 'body':fh.read(), 'created':modification_date(filename), })
            except Exception, e:
                logging.debug(row)
                pass
                # raise e

            fh.close()
            # break


class Import(myRequestHandler):
    """

    """

    def get(self):
        filelisting = "/Users/michelek/amphora-xmls.lst"
        fh = open(filelisting)
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

        self.db = connection()

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
                    self.db.execute(sql)
                except Exception, e:
                    logging.debug(sql)
                    logging.debug(e)


handlers = [
    ('/amphora/import', Import),
    ('/amphora/loadfiles', LoadFiles),
]
