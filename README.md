# pinscrapy
A crawler that scrapes [Pinboard](https://pinboard.in) bookmarks recursively.  The algorithm works as follows:

1. It starts with a user and scrapes all bookmarks
2. For each bookmark, identified by a url_slug, it finds all users that have also saved the same bookmark.
3. For each user from step 2, it repeats the process (go to 1, ...)

The output is a item that contains information for each bookmark and a second one that contains the list of users who pinned each of those bookmarks. This item is stored either locally or on S3 as a json or parque file or in a MongoDB collection.
