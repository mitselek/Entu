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


class Import(myRequestHandler):
    """

    """

    def get(self):
        fileroot = '/Users/michelek/Documents/library import/'

        # # self.write('<h1>TagType.xml</h1>')
        # tagtype_file = fileroot + 'TagType.xml'
        # fh = open(tagtype_file)
        # tagtype_xml = xmltodict.parse(fh.read())['entities'] #['entity']
        # fh.close()

        # sql_set = []
        # for tt in tagtype_xml['entity']:
        #     sql_part = []
        #     sql_part.append(u"`key` = '%s'" % tt['@key'])
        #     for pr in tt['property']:
        #         sql_part.append(u"%s = '%s'" % (pr['@name'], pr['#text'].replace("'","\\\'")))

        #     self.write('<br/>INSERT INTO x_arxapp_tagtype SET ' + ', '.join(sql_part) + ';')

        # # self.write('<h1>Tag.xml</h1>')
        # tag_file = fileroot + 'Tag.xml'
        # fh = open(tag_file)
        # tag_xml = xmltodict.parse(fh.read())['entities'] #['entity']
        # fh.close()

        # sql_set = []
        # for tt in tag_xml['entity']:
        #     sql_part = []
        #     sql_part.append(u"`key` = '%s'" % tt['@key'])
        #     for pr in tt['property']:
        #         sql_part.append(u"%s = '%s'" % (pr['@name'], pr['#text'].replace("'","\\\'")))

        #     self.write('<br/>INSERT INTO x_arxapp_tag SET ' + ', '.join(sql_part) + ';')

        # # self.write('<h1>Item.xml</h1>')
        # item_file = fileroot + 'Item.xml'
        # fh = open(item_file)
        # item_xml = xmltodict.parse(fh.read())['entities'] #['entity']
        # fh.close()

        # sql_set = []
        # for tt in item_xml['entity']:
        #     tag_item = []
        #     sql_part = []
        #     sql_part.append(u"`key` = '%s'" % tt['@key'])
        #     for pr in tt['property']:
        #         if pr['@name'] == 'tags':
        #             tag_item.append("<br/>INSERT INTO x_arxapp_tag_item SET tag = '%s', item = '%s';" % (pr['#text'], tt['@key']))
        #         else:
        #             sql_part.append(u"%s = '%s'" % (pr['@name'], pr['#text'].replace("'","\\\'")))

        #     self.write('<br/>INSERT INTO x_arxapp_item SET ' + ', '.join(sql_part) + ';')
        #     self.write(''.join(tag_item))

        # self.write('<h1>Copy.xml</h1>')
        copy_file = fileroot + 'Copy.xml'
        fh = open(copy_file)
        copy_xml = xmltodict.parse(fh.read())['entities'] #['entity']
        fh.close()

        sql_set = []
        for tt in copy_xml['entity']:
            sql_part = []
            sql_part.append(u"`key` = '%s'" % tt['@key'])
            for pr in tt['property']:
                sql_part.append(u"%s = '%s'" % (pr['@name'], pr['#text'].replace("'","\\\'")))

            self.write('<br/>INSERT INTO x_arxapp_copy SET ' + ', '.join(sql_part) + ';')

        return


handlers = [
    ('/arxapp/import', Import),
]
