Duplicate and Deleted File Tracker is command line application for determining 
whether files newely added to an archive are duplicates of existing files or of 
files which were previously deleted from the archive.

Requires a postgreSQL database be setup (tested on version 14). The details of this, 
along with the path of the root folder of the target file archive should be entered 
into 'duplicateAndDeletedFileTracker\config.py'
according to the structure in 'duplicateAndDeletedFileTracker\config_TEMPLATE.py'.

Example use case:
1) Set photo archive path as rootPath in config.
2) Run resetDatabase.py in order to setup the database for the first time.
3) Run main.py in order to log the current state of the database.
4) Add photos from phone to photo archive in a new folder.
5) Run main.py to remove all duplicates.
6) Manually sort the photos and delete ones you don't want to keep.
7) Run main.py to log which photos were moved / deleted.
8) At a later date, add photos from phone again.
9) Run main.py to remove duplicates and photos the user previously decide to delete, leaving them with just the new photos from their phone.