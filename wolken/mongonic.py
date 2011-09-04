#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses.

__version__ = "0.2"

from wolken import Struct
import gridfs

class GridFS:
    '''an extended GridFS (+MongoDB) backend to update metadata in a separate
    MongoDB but handle them in one GridOut object.
    
    As it is not documented: every attribute in GridOut is read-only. You
    can only write these `metadata` once. This extended GridFS will keep
    GridIn's _id, content_type, filename and upload_date and so on intact
    and read-only!'''
    
    def __init__(self, database, collection='fs'):
        
        self.mdb = database.items
        self.gfs = gridfs.GridFS(database, collection)
        
    def put(self, data, _id, content_type, filename, **kw):
        
        item_type = content_type.split('/', 1)[0]
        if not item_type in ['image', 'text', 'archive', 'audio', 'video']:
            item_type = 'unknown'
        
        _id = self.gfs.put(data, _id=_id, content_type=content_type,
                           filename=filename)
        if not kw:
            kw = {}
        kw.update({'_id': _id, 'item_type': item_type})
        self.mdb.insert(kw)
            
        return _id
            
    def get(self, _id=None, short_id=None):
        '''if url is given, we need a reverse lookup in metadata.  Returns
        a GridOut with additional metadata added.'''

        if _id:
            cur = self.mdb.find_one({'_id': _id})
        else:
            cur = self.mdb.find_one({'short_id': short_id})
            if not cur:
                raise gridfs.errors.NoFile
            _id = cur['_id']
        
        if cur.get('item_type', '') == 'bookmark':
            return Struct(**cur)
        else:
            obj = self.gfs.get(_id)
            obj.__dict__.update(cur)
            return obj
            
    def update(self, _id, **kw):
        '''update **kw'''
        self.mdb.update({'_id': _id}, {'$set': kw}, upsert=False)