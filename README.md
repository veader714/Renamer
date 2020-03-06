# Renamer

The basic idea behind this is to create a program that will be able to run on a downloaded folder and Identify the media.

TODO: A lot....

1. TVDB proper error handling
2. Proper episode season and number detection
    - Unknown formats
    - XXX format
    - episode xxx format
3. Should this move files or should megaGet server do that???
4. DB for current show and ep info (RO on renamer and write on megaGet server)
5. Renamer should be able to work independently of both the server and DB.
6. Commandline tools
7. Handle multiple TV shows
8. Popping episode titles from the filename string could probably be done via a tree
    that identifies the 'center' of the episode string and splits via a separator/title
    thing. First need to identify which seperators do what....separators of episode titles vs seperators of individual strings... seperators and episode name hierarchy. A text blob at the very bottom, then a sub seperator would be lower in rank than an episode title, which is lower than a primary seperator. We can first test episode titles and if we get bad scores, then we can start building up string chunks. This should speed up 99th percentile of guesses where we have to build up a string and check as we build.
9. It would be nice to keep a list of chunks that have very poor scores to help remove extra crap