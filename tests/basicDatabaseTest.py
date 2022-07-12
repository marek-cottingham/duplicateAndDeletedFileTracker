import datetime
import unittest

from archiveDatabase import config, queries
from archiveDatabase.main import (CursorInterface, loadCurrentFiles,
                                  openConnection, prettyPrint, updateModifiedFilesHash,
                                  updateNewFilesHash)

from tests import test_queries
from tests.test_config import config
from tests.expected_tables import currentFiles_expected_tables

class archiveDatabaseTestCase(unittest.TestCase):
    def test_canConnect(self):
        with openConnection(config.connect) as cursor:
            pass

    def test_createTable_and_persistentInsert(self):
        with openConnection(config.connect) as cursor:
            self.setup_db_for_test(cursor)
            
            cursor.execute("INSERT INTO currentFiles (relative_path) VALUES ('test')")

            cursor.execute(queries.selectAllCurrentFiles)
            self.assertEqual(cursor.fetchall()[0][1],'test')

        with openConnection(config.connect) as cursor:
            cursor.execute(queries.selectAllCurrentFiles)
            self.assertEqual(cursor.fetchall()[0][1],'test')

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

    def setup_db_for_test(self, cursor: CursorInterface):
        cursor.execute(queries.resetAll)
        cursor.execute(queries.resetCurrentFiles)
        cursor.execute(test_queries.setupTest_archiveFiles)

    def setup_with_hash_reading(self, cursor: CursorInterface):
        self.setup_db_for_test(cursor)
        loadCurrentFiles(cursor, config.rootPath)
        updateNewFilesHash(cursor, config.rootPath)
        updateModifiedFilesHash(cursor, config.rootPath)
        

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


    def test_selectViewsCurrentFiles(self):
        with openConnection(config.connect) as cursor:
            self.setup_with_hash_reading(cursor)

            for relative_path, view_dict in currentFiles_expected_tables.items():
                for view, isInView in view_dict.items():
                    cursor.execute(f"SELECT relative_path FROM {view}")
                    result = cursor.fetchall()
                    if isInView:
                        self.assertIn((relative_path,),result)
                    else:
                        self.assertNotIn((relative_path),result)


            # prettyPrint(cursor, "SELECT * FROM duplicateFiles")
            # prettyPrint(cursor, "SELECT * FROM movedFiles")
            # prettyPrint(cursor, "SELECT * FROM newUnseenFiles")
            # prettyPrint(cursor, "SELECT * FROM modifiedFiles")
            # prettyPrint(cursor, "SELECT * FROM modifiedContentsFiles")