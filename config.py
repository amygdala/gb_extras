
"""Contains config variables for the app."""

INDEX_NAME = "gb2"  # The name of the search index that the app uses.
NNTP_SERVER = "news.mixmin.net"
NEWSGROUPS = ["sci.physics", "sci.archaeology", "sci.math", "sci.lang"]
NUM_ENTRIES = 4 # number of recent guestbook entries listed
# The lat/long of a center point against which example guestbook entry locations
# will be generated.  You may want to set this to near your current location, so
# so that a geosearch against your location (as indicated by your browser) will
# come up with some entries.
GEOBASE = [-33.87, 151]
