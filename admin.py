#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Defines an admin handler to reset app data."""

import logging

import webapp2

import config
import models

from google.appengine.api import search
from google.appengine.ext import ndb


class ClearData(webapp2.RequestHandler):
  """Clear app data, both documents from the search index and Greeting entities
  in the datastore."""

  def get(self):
    """Clear app data."""
    index = search.Index(name=config.INDEX_NAME)
    try:
      while True:
        # until no more documents, get a list of documents,
        # constraining the returned objects to contain only the doc ids,
        # extract the doc ids, and delete the docs.
        document_ids = [document.doc_id
                        for document in index.list_documents(ids_only=True)]
        if not document_ids:
          break
        index.remove(document_ids)
    except search.Error:
      logging.exception('Error removing documents.')
      self.response.write('Error clearing search index documents.')
      return
    try:
      greetings_keys = models.Greeting.query().fetch(keys_only=True)
      ndb.delete_multi(greetings_keys)
    except:
      logging.exception('Error removing Greeting entities.')
      self.response.write('Error removing app data.')
      return
    self.response.write('All clear...')

app = webapp2.WSGIApplication([
    ('/admin/clear', ClearData)
])
