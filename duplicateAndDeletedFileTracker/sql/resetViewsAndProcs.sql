-- Current files whose relative_path doesn't match a file in archiveFiles
CREATE OR REPLACE VIEW newPathFiles AS
SELECT curr.*
FROM currentFiles curr
LEFT JOIN archiveFiles arch USING (relative_path)
WHERE arch.relative_path IS NULL;

CREATE OR REPLACE VIEW newPathFilesWithoutHash AS 
SELECT *
FROM newPathFiles
WHERE file_hash IS NULL;

CREATE OR REPLACE VIEW newUnseenFiles AS
SELECT new.*
FROM newPathFiles new
LEFT JOIN archiveFiles arch USING (file_hash)
LEFT JOIN archiveDeletedFiles archDel USING (file_hash)
WHERE arch.file_hash IS NULL
	AND archDel.file_hash IS NULL
	AND new.file_hash IS NOT NULL;

-- New path files whose hash matches an existing file
CREATE OR REPLACE VIEW hashMatchesArchiveFiles AS
SELECT new.*, arch.relative_path as original_path
FROM newPathFiles new
INNER JOIN archiveFiles arch USING (file_hash);

CREATE OR REPLACE VIEW movedFiles as
SELECT hm.file_id, hm.relative_path, hm.file_hash, hm.modified, hm.original_path
FROM hashMatchesArchiveFiles hm
LEFT JOIN currentFiles curr
	ON hm.original_path = curr.relative_path
WHERE curr.relative_path IS NULL
OR curr.file_hash <> hm.file_hash; -- New file at orignal location edge case

CREATE OR REPLACE VIEW duplicateFiles as
SELECT hashMatch.*
FROM hashMatchesArchiveFiles hashMatch
LEFT JOIN movedFiles moved
	ON hashMatch.original_path = moved.original_path
WHERE moved.original_path IS NULL;

-- Files where "modified" has changed compared to file in archiveFiles with 
-- 	same relative_path
CREATE OR REPLACE VIEW modifiedFiles AS
SELECT curr.*, arch.file_id as arch_id, arch.file_hash as arch_hash, arch.modified as arch_modified
FROM currentFiles curr
INNER JOIN archiveFiles arch
	ON curr.relative_path = arch.relative_path
WHERE
	curr.modified <> arch.modified;

CREATE OR REPLACE VIEW modifiedMetaFiles AS
SELECT * FROM modifiedFiles
WHERE file_hash = arch_hash;

CREATE OR REPLACE VIEW modifiedContentsFiles AS
SELECT * FROM modifiedFiles
WHERE file_hash <> arch_hash;

CREATE OR REPLACE VIEW deletedFiles AS
SELECT arch.* 
FROM archiveFiles arch
LEFT JOIN currentFiles curr
	ON arch.relative_path = curr.relative_path
LEFT JOIN movedFiles mv
	ON arch.relative_path = mv.original_path
WHERE curr.relative_path IS NULL
AND mv.original_path IS NULL;

CREATE OR REPLACE VIEW duplicatePreviouslyDeletedFiles AS
SELECT curr.*, archDel.relative_path as previously_deleted_path
FROM currentFiles curr
INNER JOIN archiveDeletedFiles archDel
	ON archDel.file_hash = curr.file_hash;

CREATE OR REPLACE VIEW duplicatesInArchive AS
SELECT arch1.*, arch2.relative_path as duplicate_path
FROM archiveFiles arch1
INNER JOIN archiveFiles arch2 USING (file_hash)
WHERE arch1.file_id <> arch2.file_id;

CREATE OR REPLACE PROCEDURE updateArchiveMovedFiles() 
LANGUAGE plpgsql
AS $$
BEGIN
	UPDATE archiveFiles arch
	SET	relative_path = mv.relative_path, modified = mv.modified
	FROM movedFiles mv
	WHERE arch.relative_path = mv.original_path;
END; $$;
 
CREATE OR REPLACE PROCEDURE updateArchiveModifiedFiles()
LANGUAGE plpgsql
AS $$
BEGIN
	UPDATE archiveFiles arch
	SET modified = mod.modified, file_hash = mod.file_hash
	FROM modifiedFiles mod
	WHERE arch.relative_path = mod.relative_path;
END; $$;

CREATE OR REPLACE PROCEDURE updateArchiveNewUnseenFiles()
LANGUAGE plpgsql
AS $$
BEGIN
	INSERT INTO archiveFiles (relative_path, file_hash, modified)
	SELECT relative_path, file_hash, modified 
	FROM newUnseenFiles;
END; $$;

CREATE OR REPLACE PROCEDURE updateArchiveDeletedFiles()
LANGUAGE plpgsql
AS $$
BEGIN
	INSERT INTO archiveDeletedFiles (relative_path, file_hash, modified, deleteDetected)
	SELECT relative_path, file_hash, modified, now() 
	FROM deletedFiles;
	DELETE FROM archiveFiles
	WHERE file_id
	IN (SELECT file_id FROM deletedFiles);
END; $$;

CREATE OR REPLACE PROCEDURE keepDuplicate(input_id int)
LANGUAGE plpgsql
AS $$
BEGIN
	INSERT INTO archiveFiles (relative_path, file_hash, modified)
	SELECT relative_path, file_hash, modified
	FROM duplicateFiles
	WHERE file_id = input_id; 
END; $$;

CREATE OR REPLACE PROCEDURE keepAllDuplicates()
LANGUAGE plpgsql
AS $$
BEGIN
	INSERT INTO archiveFiles (relative_path, file_hash, modified)
	SELECT relative_path, file_hash, modified
	FROM duplicateFiles;
END; $$;

CREATE OR REPLACE PROCEDURE removeDuplicate(input_id int)
LANGUAGE plpgsql
AS $$
BEGIN
	DELETE FROM currentFiles
	WHERE file_id = input_id; 
END; $$;

CREATE OR REPLACE PROCEDURE removeAllDuplicates()
LANGUAGE plpgsql
AS $$
BEGIN
	DELETE FROM currentFiles
	USING duplicateFiles
	WHERE currentFiles.file_id = duplicateFiles.file_id;
END; $$;

CREATE OR REPLACE PROCEDURE keepDuplicateDeleted(input_id int)
LANGUAGE plpgsql
AS $$
BEGIN
	INSERT INTO archiveFiles (relative_path, file_hash, modified)
	SELECT relative_path, file_hash, modified
	FROM duplicatePreviouslyDeletedFiles
	WHERE file_id = input_id; 
END; $$;

CREATE OR REPLACE PROCEDURE keepAllDuplicatesDeleted()
LANGUAGE plpgsql
AS $$
BEGIN
	INSERT INTO archiveFiles (relative_path, file_hash, modified)
	SELECT relative_path, file_hash, modified
	FROM duplicatePreviouslyDeletedFiles;
END; $$;

CREATE OR REPLACE PROCEDURE removeAllDuplicatesDeleted()
LANGUAGE plpgsql
AS $$
BEGIN
	DELETE FROM currentFiles
	USING duplicatePreviouslyDeletedFiles dpdf
	WHERE currentFiles.file_id = dpdf.file_id;
END; $$;