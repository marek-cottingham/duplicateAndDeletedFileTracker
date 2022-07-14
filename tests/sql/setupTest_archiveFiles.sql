INSERT INTO archiveFiles (relative_path, modified, file_hash) VALUES
    ('present.txt', '2022-07-12 07:20:00', '43f9b89c0b9d22d8110ead813ea3949f20592a8bfc3c777d2d49e64da3b0cc9b'),
    ('foxtrot\present_hasDup.txt', '2022-07-12 07:19:53', '740ad0f2a20c5d4167f7a299aaa044ffddd1ea82a290cfbdcf0eefb27da342d5'),
    ('alpha\movedFile.txt', '2022-07-12 07:49:22', 'b11c9047f3512271a5cbbe3040a2628206e1d95765b288cf03affcae5edbb457'),
    ('alpha\deletedFile.txt', '2022-07-12 07:49:22', '00009047f3512271a5cbbe3040a2628206e1d95765b288cf03affcae5edbb457'),
    ('alpha\bravo\modified.txt', '2022-07-12 16:30:00', '00005dcaf408935ff76747226d2e8bee4319a2f593c1d7a838115e56183d1f37'),
    ('alpha\bravo\moved-newOrginalLoc.txt', '2022-07-12 18:53:09', '398cd4bb92ec6b4f408cd46c96cfe7442445a94b3fa92d236debd5d567492e23')
    ;

INSERT INTO archiveDeletedFiles (relative_path, modified, file_hash, deleteDetected) VALUES
    ('previouslyDeleted.txt', '2022-07-01 07:20:00', '52ec1d2e53cb1f7d4458626db4980fcb04a80233aff75a4b65df6ca184b918d9', '2022-07-12 07:20:00')