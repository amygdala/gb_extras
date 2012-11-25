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

"""Contains the non-admin ('user-facing') request handlers for the app."""

import json
import logging
import nntplib
import os
import random
import urllib
import wsgiref

import jinja2
import webapp2

import config
import models

from google.appengine.api import search
from google.appengine.api import users
from google.appengine.ext import ndb

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class MainPage(webapp2.RequestHandler):

  def get(self):
    """Display the main page, including the most recent guestbook entries
    for the current guestbook."""
    app_url = wsgiref.util.application_uri(self.request.environ)
    guestbook_name = self.request.get('guestbook_name').strip()
    ancestor_key = ndb.Key('Book', guestbook_name or '*notitle*')
    # Fetch the most recent Greeting entities that are children of the given
    # guestbook parent.
    greetings_future = models.Greeting.query_book(ancestor_key).fetch_async(
        config.NUM_ENTRIES, projection=[models.Greeting.content,
                                        models.Greeting.author])
    # build the login/logout link info
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    greetings = greetings_future.get_result()

    template_values = {
        'greetings': greetings,
        'url': url,
        'url_linktext': url_linktext,
        'guestbook_name': guestbook_name,
        'app_url': app_url
    }

    template = jinja_environment.get_template('index.html')
    self.response.write(template.render(template_values))


class GuestbookPost(webapp2.RequestHandler):
  """The GuestbookPost handler is called when the guestbook entry form is
  submitted."""

  def get_content_snippet(self):
    """Get some text from a randomly-selected newsgroup article.  Shows the use
    of the Socket API, which is used by nntplib.  Requires that the app be
    whitelisted to use the Socket API."""
    dtext = ''
    try:
      NNTP_SERVER = config.NNTP_SERVER
      # get an nntp server object
      s = nntplib.NNTP(NNTP_SERVER)
      # randomly select a newsgroup name from a list.
      newsgroup = config.NEWSGROUPS[random.randrange(0, len(config.NEWSGROUPS))]
      logging.debug('using newsgroup: %s', newsgroup)
      _, _, first, last, _ = s.group(newsgroup)
      # get a random article id, then get the article corresponding to the id.
      item_num = str(random.randrange(int(first), int(last)))
      _, items = s.xover(item_num, item_num)
      for (article_id, _, _, _, _, _,
           _, _) in items:
        _, _, _, text = s.article(article_id)
        snippet = text[-7:-4]  # grab some text towards the end of the article
        # build a string form the article text-- quick-and-dirty content
        # generation.
        dtext = ' '.join(snippet)
        try:
          dtext = dtext.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
          logging.exception('error on: %s', dtext)
    except:
      logging.exception('error generating content snippet')
    logging.debug('content snippet: %s', dtext)
    return dtext

  @ndb.toplevel
  def post(self):
    """This handler is called when the guestbook entry form is submitted."""
    guestbook_name = self.request.get('guestbook_name').strip()
    content = self.request.get('content')
    # if the user requested auto-generated content
    if self.request.get('autogen'):
      # then grab some content from a random newsgroup post
      content = self.get_content_snippet()
    # We set the parent key on each 'Greeting' to ensure each guestbook's
    # greetings are in the same entity group.
    greeting = models.Greeting(
        parent=ndb.Key('Book', guestbook_name or '*notitle*'),
        content=content)
    if users.get_current_user():
      greeting.author = users.get_current_user()
    # do the datastore put asynchronously, rather than blocking.
    greeting.put_async()
    # create and index Search document with content text.  For this simple demo,
    # swallow any indexing errors.
    self.create_search_document(content, guestbook_name, greeting.author)
    # the method decorator ensures that we've finished the async put
    # before method return.
    self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}))

  def create_search_document(self, content, gb_name, author):
    """Using the Search API, create and index a document containing the
    guestbook post information. The document includes post location information,
    which will let us perform geosearches over the indexed guestbook posts.
    For demo purposes, a location will be randomly generated, but
    for a real app, this information would be obtained from the client."""
    if content:
      index = search.Index(name=config.INDEX_NAME)
      if author:
        name = author.nickname()
      else:
        name = 'anonymous'
      # generate a random location in an area (default: around Sydney) for demo
      # porpoises.  Create a GeoPoint with the generated lat/long values.
      geopoint = search.GeoPoint(config.GEOBASE[0] + random.uniform(-.3, .3),
                                 config.GEOBASE[1] + random.uniform(-.3, .3))
      fields = [search.TextField(name='content', value=content),
                search.TextField(name='author', value=name),
                search.GeoField(name='author_location', value=geopoint),
                search.TextField(name='guestbook', value=gb_name)]
      try:
        # create a search document using the fields list that we built, and
        # index it.
        d = search.Document(fields=fields)
        res = index.add(d)
        return res
      except search.Error:
        logging.exception('Error adding doc %s', d)
        return None
    else:
      return None


class SearchNearby(webapp2.RequestHandler):
  """Search for nearby guestbook entries."""

  def render_json(self, response):
    self.response.write('%s(%s);' % (self.request.GET['callback'],
                                     json.dumps(response)))

  def get(self):
    """Search for nearby guestbook entries, and return the results as JSON."""
    results = self.search_nearby()
    response_obj = []
    try:
      for doc in results:
        try:
          gb = doc.field('guestbook').value
        except ValueError:
          gb = 'default'
        logging.debug('guestbook: [%s]', gb)
        geopoint = doc.field('author_location').value
        logging.info('geopoint: %s', geopoint)
        resp = {'post_content': ('guestbook: %s:<br/>%s'
                                 % (gb, doc.field('content').value)),
                'author': doc.field('author').value,
                'lat': geopoint.latitude, 'lon': geopoint.longitude}
        response_obj.append(resp)
      logging.debug('resp: %s', response_obj)
    except:
      logging.exception('error processing search results.')
    self.render_json(response_obj)

  def search_nearby(self):
    """Use the Search API's geosearch capabilities to look for guestbook entries
    near the user, based on lat/long info obtained from the client."""
    doc_limit = 20
    query = self.request.get('location_query')
    lat = self.request.get('latitude')
    lon = self.request.get('longitude')
    # the location query from the client will have this general form:
    # <query terms> distance(author_location,
    #   geopoint(37.7899528, -122.3908226)) < 40000
    logging.debug('location query: %s, lat %s, lon %s', query, lat, lon)
    try:
      index = search.Index(name=config.INDEX_NAME)
      # sort results by distance
      loc_expr = 'distance(author_location, geopoint(%s, %s))' % (lat, lon)
      sortexpr = search.SortExpression(
          expression=loc_expr,
          direction=search.SortExpression.ASCENDING, default_value=0)
      sortopts = search.SortOptions(expressions=[sortexpr])
      # Build the search query using the constructed sort options.
      search_query = search.Query(
          query_string=query.strip(),
          options=search.QueryOptions(
              limit=doc_limit,
              sort_options=sortopts,
              ))
      return index.search(search_query)
    except search.Error:
      logging.exception('There was a search error:')
      self.render_json([])
      return None


