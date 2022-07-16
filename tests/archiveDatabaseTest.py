import builtins
import datetime
from pathlib import Path
import shutil
import unittest
from unittest.mock import MagicMock, patch

from duplicateAndDeletedFileTracker import config, queries
from duplicateAndDeletedFileTracker.main import (CursorInterface, ExtendedCursorInterface, getDuplicateManagementCallbacks, loadCurrentFiles,
                                  openConnection, prettyPrint, printDuplicateInstructions, updateModifiedFilesHash,
                                  updateNewFilesHash, promptUserDuplicates)

from tests import test_queries
from tests.test_config import config
from tests.expected_tables import expected_tables

class archiveDatabaseTestCase(unittest.TestCase):
    def setup_db_for_test(self, cursor: CursorInterface):
        cursor.execute(queries.resetAllTables)
        cursor.execute(queries.resetCurrentFiles)
        cursor.execute(queries.resetViewAndProcs)
        cursor.execute(test_queries.setupTest_archiveFiles)
        shutil.rmtree(config.rootPath)
        shutil.copytree(config.fileStructurePath, config.rootPath, dirs_exist_ok=True)

    def setup_with_hash_reading(self, cursor: CursorInterface):
        self.setup_db_for_test(cursor)
        loadCurrentFiles(cursor, config.rootPath)
        updateNewFilesHash(cursor, config.rootPath)
        updateModifiedFilesHash(cursor, config.rootPath)

    def setup_with_updateArchive(self, cursor: CursorInterface):
        self.setup_with_hash_reading(cursor)
        cursor.execute("CALL updateArchiveMovedFiles();")
        cursor.execute("CALL updateArchiveModifiedFiles();")
        cursor.execute("CALL updateArchiveNewUnseenFiles();")
        cursor.execute("CALL updateArchiveDeletedFiles();")

    def assertPathInTable(self, cursor: ExtendedCursorInterface, filePath: str, table: str):
        result = cursor.getResult(f"SELECT relative_path FROM {table}")
        self.assertIn((filePath,),result)

    def assertPathNotInTable(self, cursor: ExtendedCursorInterface, filePath: str, table: str):
        result = cursor.getResult(f"SELECT relative_path FROM {table}")
        self.assertNotIn((filePath,),result)

    def assertEmptyTable(self, cursor: ExtendedCursorInterface, table: str):
        result = cursor.getResult(f"SELECT * FROM {table}")
        self.assertEqual(result, [])

    def pretty_print_all_views(self, cursor: CursorInterface):
        for view in (
                'duplicateFiles',
                'newUnseenFiles',
                'modifiedFiles',
                'movedFiles',
                'archiveFiles',
                'deletedFiles',
                'duplicatePreviouslyDeletedFiles',
            ):
                prettyPrint(cursor, f'SELECT * FROM {view}')

    def test_canConnect(self):
        with openConnection(config.connect) as cursor:
            pass

    def test_createTable_and_persistentInsert(self):
        with openConnection(config.connect) as cursor:
            self.setup_db_for_test(cursor)
            
            cursor.execute("INSERT INTO currentFiles (relative_path) VALUES ('test')")

            self.assertPathInTable(cursor, 'test', "currentFiles")
        with openConnection(config.connect) as cursor:
            self.assertPathInTable(cursor, 'test', "currentFiles")

    def test_loadCurrentFiles(self):
        with openConnection(config.connect) as cursor:
            self.setup_db_for_test(cursor)

            loadCurrentFiles(cursor, config.rootPath)

            result = cursor.getResult("SELECT relative_path, modified FROM currentFiles")
            for element in [
                ('present.txt', datetime.datetime(2022, 7, 12, 7, 20)),
                ('alpha\\new_isDup.txt', datetime.datetime(2022, 7, 12, 7, 19, 46)),
                ('alpha\\bravo\\new.txt', datetime.datetime(2022, 7, 12, 7, 20, 5)),
                ('foxtrot\\present_hasDup.txt', datetime.datetime(2022, 7, 12, 7, 19, 53))
            ]:
                self.assertIn(element, result)
        
    def test_update_newPathFiles_and_modifiedFiles_hashes(self):
        with openConnection(config.connect) as cursor:
            self.setup_db_for_test(cursor)
            loadCurrentFiles(cursor, config.rootPath)

            updateNewFilesHash(cursor, config.rootPath)
            updateModifiedFilesHash(cursor, config.rootPath)

            result = cursor.getResult("SELECT relative_path, file_hash FROM currentFiles")
            for element in [
                ('alpha\\new_isDup.txt', '740ad0f2a20c5d4167f7a299aaa044ffddd1ea82a290cfbdcf0eefb27da342d5'),
                ('alpha\\bravo\\modified.txt', 'e8ce5dcaf408935ff76747226d2e8bee4319a2f593c1d7a838115e56183d1f37')
            ]:
                self.assertIn(element, result)


    def test_selectViews(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            for relative_path, view_dict in expected_tables.items():
                for view, isInView in view_dict.items():
                    if isInView:
                        self.assertPathInTable(cursor, relative_path, view)
                    else:
                        self.assertPathNotInTable(cursor, relative_path, view)

    def test_updateArchiveMovedFiles(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            cursor.execute("CALL updateArchiveMovedFiles();")

            self.assertEmptyTable(cursor,"movedFiles")
            self.assertPathInTable(cursor,'foxtrot\\movedFile.txt',"archiveFiles")
            self.assertPathNotInTable(cursor,'alpha\\movedFile.txt',"archiveFiles")
            self.assertPathInTable(cursor,'foxtrot\\movedWithNewAtOrginalLoc.txt',"archiveFiles")
            self.assertPathNotInTable(cursor,'alpha\\bravo\\moved-newOrginalLoc.txt',"archiveFiles")

            # In the case where a new file is created at the moved file's 
            # orignal location, this file should now be treated 
            # as newUnseenFile, not modifiedFile.

            self.assertPathInTable(cursor,"alpha\\bravo\\moved-newOrginalLoc.txt","newUnseenFiles")
            self.assertPathNotInTable(cursor,"alpha\\bravo\\moved-newOrginalLoc.txt","modifiedFiles")

    def test_updateArchiveModifiedFiles(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)
            cursor.execute("CALL updateArchiveMovedFiles();")

            cursor.execute("CALL updateArchiveModifiedFiles();")

            self.assertEmptyTable(cursor,"modifiedFiles")

            result = cursor.getResult("SELECT relative_path, file_hash, modified FROM archiveFiles")
            self.assertIn(
                ('alpha\\bravo\\modified.txt', 
                    'e8ce5dcaf408935ff76747226d2e8bee4319a2f593c1d7a838115e56183d1f37', 
                    datetime.datetime(2022, 7, 12, 16, 40, 42)),
                result
            )
            
    def test_updateArchiveNewUnseenFiles(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)
            cursor.execute("CALL updateArchiveMovedFiles();")
            cursor.execute("CALL updateArchiveModifiedFiles();")

            cursor.execute("CALL updateArchiveNewUnseenFiles();")

            self.assertPathInTable(cursor,"alpha\\bravo\\new.txt","archiveFiles")
            self.assertEmptyTable(cursor, "newUnseenFiles")

    def test_updateArchiveDeletedFiles(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)
            cursor.execute("CALL updateArchiveMovedFiles();")
            cursor.execute("CALL updateArchiveModifiedFiles();")
            cursor.execute("CALL updateArchiveNewUnseenFiles();")

            cursor.execute("CALL updateArchiveDeletedFiles();")

            self.assertEmptyTable(cursor, "deletedFiles")
            self.assertPathNotInTable(cursor, "alpha\\deletedFile.txt", "archiveFiles")
            self.assertPathInTable(cursor, "alpha\\deletedFile.txt", "archiveDeletedFiles")

    def test_keepAllDuplicates(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            cursor.execute("CALL keepAllDuplicates();")

            self.assertEmptyTable(cursor, "duplicateFiles")
            self.assertPathInTable(cursor, "alpha\\new_isDup.txt", "archiveFiles")

    def test_keepDuplicateById(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            file_id = cursor.getResult(
                "SELECT file_id FROM duplicateFiles WHERE relative_path = 'alpha\\new_isDup.txt'"
                )[0][0]
            cursor.execute("call keepDuplicate(%s)",(file_id,))

            self.assertPathNotInTable(cursor, "alpha\\new_isDup.txt", "duplicateFiles")
            self.assertPathInTable(cursor, "alpha\\new_isDup.txt", "archiveFiles")

    def test_keepDuplicateByIdSafeToPassNone(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            cursor.execute("call keepDuplicate(%s)",(None,))

    def test_removeAllDuplicates(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            r_all = getDuplicateManagementCallbacks(
                cursor, "duplicateFiles", config.rootPath)["rall"]
            r_all()

            self.assertEmptyTable(cursor, "duplicateFiles")
            self.assertPathNotInTable(cursor, "alpha\\new_isDup.txt", "archiveFiles")
            self.assertFalse(Path(config.rootPath, "alpha\\new_isDup.txt").exists())

    def test_removeDuplicateById(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            r_id = getDuplicateManagementCallbacks(cursor, "duplicateFiles", config.rootPath)["r###"]
            file_id = cursor.getResult(
                "SELECT file_id FROM duplicateFiles WHERE relative_path = 'alpha\\new_isDup.txt'"
                )[0][0]
            r_id(file_id)

            self.assertPathNotInTable(cursor, "alpha\\new_isDup.txt", "currentFiles")
            self.assertPathNotInTable(cursor, "alpha\\new_isDup.txt", "archiveFiles")
            self.assertFalse(Path(config.rootPath, "alpha\\new_isDup.txt").exists())

    def test_removeAllDuplicatesPreviouslyDelected(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            r_all = getDuplicateManagementCallbacks(
                cursor, "duplicatePreviouslyDeletedFiles", config.rootPath)["rall"]
            r_all()

            self.assertEmptyTable(cursor, "duplicatePreviouslyDeletedFiles")
            self.assertPathNotInTable(cursor, "foxtrot\\dupPreviouslyDeleted.txt", "archiveFiles")
            self.assertFalse(Path(config.rootPath, "foxtrot\\dupPreviouslyDeleted.txt").exists())
    

    

    









