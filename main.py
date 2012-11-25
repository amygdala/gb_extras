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

"""Defines the routing for the app's user-facing handlers.
See the README file for information on what this app does."""

import webapp2

import handlers

app = webapp2.WSGIApplication([
    ('/', handlers.MainPage),
    ('/sign', handlers.GuestbookPost),
    ('/get_nearby', handlers.SearchNearby),
])


