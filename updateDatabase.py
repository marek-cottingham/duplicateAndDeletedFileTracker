
from duplicateAndDeletedFileTracker import config, queries
from duplicateAndDeletedFileTracker.main import (getDuplicateManagementCallbacks,
                                  loadCurrentFiles, openConnection, prettyPrint,
                                  promptUserDuplicates,
                                  updateModifiedFilesHash, updateNewFilesHash)

with openConnection(config.connect) as cursor:
    cursor.execute(queries.resetCurrentFiles)
    cursor.execute(queries.resetViewAndProcs)

    loadCurrentFiles(cursor, config.rootPath)
    updateNewFilesHash(cursor, config.rootPath)
    updateModifiedFilesHash(cursor, config.rootPath)

    prettyPrint(cursor, "SELECT relative_path, original_path FROM movedFiles")
    cursor.execute("CALL updateArchiveMovedFiles();")

    prettyPrint(cursor, "SELECT relative_path FROM modifiedFiles")
    cursor.execute("CALL updateArchiveModifiedFiles();")

    prettyPrint(cursor, "SELECT relative_path FROM newUnseenFiles")
    cursor.execute("CALL updateArchiveNewUnseenFiles();")

    prettyPrint(cursor, "SELECT relative_path FROM deletedFiles")
    cursor.execute("CALL updateArchiveDeletedFiles();")

    callbacksDup = getDuplicateManagementCallbacks(cursor, "duplicateFiles", config.rootPath)
    callbacksPrevDup = getDuplicateManagementCallbacks(
        cursor, "duplicatePreviouslyDeletedFiles", config.rootPath)
    
    promptUserDuplicates(
        cursor, 
        "SELECT file_id, relative_path, original_path FROM duplicateFiles", 
        callbacksDup
    )

    promptUserDuplicates(
        cursor, 
        "SELECT file_id, relative_path, previously_deleted_path " \
        "FROM duplicatePreviouslyDeletedFiles", 
        callbacksPrevDup
    )

    # prettyPrint(cursor,"SELECT file_id, relative_path, duplicate_path FROM duplicatesInArchive")
