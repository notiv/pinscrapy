# pinborg
A crawler that scrapes [Pinboard](https://pinboard.in) bookmarks recursively.  The algorithm works as follows:

1. It starts with a user and scrapes all bookmarks
2. For each bookmark, identified by a url_slug, it finds all users that have also saved the same bookmark.
3. For each user from step 2, it repeats the process (go to 1, ...)

The output is a json file that contains information for each bookmark as well as a list of users who pinned each of those bookmarks.
