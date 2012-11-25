
# App Engine App: Guestbook with Search and Socket Use

This is a Google App Engine Python app.  It uses as a starting point the ever-popular "Guestbook" sample app, and modifies it to include use of the Full-Text Search API (Experimental) and the Socket API (currently in the Trusted Tester phase).

**To work properly, this application must be deployed**. It won't run properly via the dev appserver. It also requires that the **application id be whitelisted for the Socket API**.

This app— as with the original Guestbook app— allows users to create guestbook entries and display the most recent entries.

In addition, this app indexes the content of the guestbook entry text, and an entry location (lat/long), using the Search API.  Then, a user can search for guestbook entries near them.

The app also uses the Socket API to auto-generate random entry text (if requested), using content from an NNTP server.


