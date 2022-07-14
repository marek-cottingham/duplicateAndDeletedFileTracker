import builtins
import datetime
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import MagicMock, patch

from archiveDatabase import config, queries
from archiveDatabase.main import (CursorInterface, loadCurrentFiles,
                                  openConnection, prettyPrint, printDuplicateInstructions, updateModifiedFilesHash,
                                  updateNewFilesHash)

from tests import test_queries
from tests.test_config import config
from tests.expected_tables import expected_tables

class archiveDatabaseTestCase(unittest.TestCase):
    def setup_db_for_test(self, cursor: CursorInterface):
        cursor.execute(queries.resetAll)
        cursor.execute(queries.resetCurrentFiles)
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

    def assertPathInTable(self, cursor: CursorInterface, filePath: str, table: str):
        cursor.execute(f"SELECT relative_path FROM {table}")
        result = cursor.fetchall()
        self.assertIn((filePath,),result)

    def assertPathNotInTable(self, cursor: CursorInterface, filePath: str, table: str):
        cursor.execute(f"SELECT relative_path FROM {table}")
        result = cursor.fetchall()
        self.assertNotIn((filePath,),result)

    def assertEmptyTable(self, cursor: CursorInterface, table: str):
        cursor.execute(f"SELECT * FROM {table}")
        result = cursor.fetchall()
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

            cursor.execute("SELECT relative_path, modified FROM currentFiles")
            result = cursor.fetchall()
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

            cursor.execute("SELECT relative_path, file_hash FROM currentFiles")
            results = cursor.fetchall()
            for element in [
                ('alpha\\new_isDup.txt', '740ad0f2a20c5d4167f7a299aaa044ffddd1ea82a290cfbdcf0eefb27da342d5'),
                ('alpha\\bravo\\modified.txt', 'e8ce5dcaf408935ff76747226d2e8bee4319a2f593c1d7a838115e56183d1f37')
            ]:
                self.assertIn(element, results)


    def test_selectViews(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            for relative_path, view_dict in expected_tables.items():
                for view, isInView in view_dict.items():
                    if isInView:
                        self.assertPathInTable(cursor, relative_path, view)
                    else:
                        self.assertPathNotInTable(cursor, relative_path, view)

            # self.pretty_print_all_views(cursor)

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

            cursor.execute("SELECT relative_path, file_hash, modified FROM archiveFiles")
            result = cursor.fetchall()
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
            self.setup_with_updateArchive(cursor)

            cursor.execute("CALL keepAllDuplicates();")

            self.assertEmptyTable(cursor, "duplicateFiles")
            self.assertPathInTable(cursor, "alpha\\new_isDup.txt", "archiveFiles")

    def test_keepDuplicateById(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_updateArchive(cursor)

    # @patch('builtins.print')
    def skip_test_userPromptDuplicates(self):
        with openConnection(config.connect) as cursor:
            print("")
            self.setup_with_hash_reading(cursor)

            while(True):
                result = prettyPrint(cursor, "SELECT file_id, relative_path, duplicate_path FROM duplicateFiles")
                if len(result) == 0:
                    break
                printDuplicateInstructions()

                command = input(">>>")

                if (command == "exit"):
                    exit()
                if (command == "skip"):
                    break
                if (command == "kall"):
                    cursor.execute("call keepAllDuplicates()")
                    break
                if (command[0] == "k"):
                    try:
                        input_id = int(command[1:])
                        cursor.execute("call keepDuplicate(%s)",(input_id,))
                    except ValueError:
                        print("~~~ Input ID invalid ~~~")
                if (command == "rall"):
                    for file_id, relative_path, duplicate_path in result:
                        Path(config.rootPath, relative_path).unlink()
                    cursor.execute("call removeAllDuplicates()")
                    break
                if (command[0] == 'r'):
                    pass









