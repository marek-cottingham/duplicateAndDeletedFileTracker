DROP TABLE IF EXISTS currentFiles CASCADE;
DROP TABLE IF EXISTS archiveFiles CASCADE;

CREATE TABLE archiveFiles (
    file_id BIGSERIAL NOT NULL PRIMARY KEY, 
	relative_path VARCHAR NOT NULL,
	file_hash CHAR(64),
	modified TIMESTAMP(0)
);

CREATE TABLE currentFiles (
	file_id BIGSERIAL NOT NULL PRIMARY KEY, 
	relative_path VARCHAR NOT NULL,
	file_hash CHAR(64),
	modified TIMESTAMP(0)
);

-- Current files whose relative_path doesn't match a file in archiveFiles
CREATE VIEW newPathFiles AS
SELECT curr.*
FROM currentFiles curr
LEFT JOIN archiveFiles arch USING (relative_path)
WHERE arch.relative_path IS NULL;

CREATE VIEW newPathFilesWithoutHash AS 
SELECT *
FROM newPathFiles
WHERE file_hash IS NULL;

CREATE VIEW newUnseenFiles AS
SELECT new.*
FROM newPathFiles new
LEFT JOIN archiveFiles arch USING (file_hash)
WHERE arch.file_hash IS NULL
	AND new.file_hash IS NOT NULL;

-- New path files whose hash matches an existing file
CREATE VIEW hashMatchesArchiveFiles AS
SELECT new.*, arch.relative_path as duplicate_path
FROM newPathFiles new
INNER JOIN archiveFiles arch USING (file_hash);

CREATE VIEW movedFiles as
SELECT hm.file_id, hm.relative_path, hm.file_hash, hm.modified, hm.duplicate_path as orginal_path
FROM hashMatchesArchiveFiles hm
LEFT JOIN currentFiles curr
	ON hm.duplicate_path = curr.relative_path
WHERE curr.relative_path IS NULL
OR curr.file_hash <> hm.file_hash; -- New file at orignal location edge case

CREATE VIEW duplicateFiles as
SELECT hashMatch.*
FROM hashMatchesArchiveFiles hashMatch
LEFT JOIN movedFiles moved
	ON hashMatch.duplicate_path = moved.orginal_path
WHERE moved.orginal_path IS NULL;

-- Files where "modified" has changed compared to file in archiveFiles with 
-- 	same relative_path
CREATE VIEW modifiedFiles AS
SELECT curr.*, arch.file_id as arch_id, arch.file_hash as arch_hash, arch.modified as arch_modified
FROM currentFiles curr
INNER JOIN archiveFiles arch
	ON curr.relative_path = arch.relative_path
WHERE
	curr.modified <> arch.modified;

CREATE VIEW modifiedMetaFiles AS
SELECT * FROM modifiedFiles
WHERE file_hash = arch_hash;

CREATE VIEW modifiedContentsFiles AS
SELECT * FROM modifiedFiles
WHERE file_hash <> arch_hash;

CREATE OR REPLACE PROCEDURE updateArchiveMovedFiles() 
LANGUAGE plpgsql
AS $$
BEGIN
	UPDATE archiveFiles arch
	SET	relative_path = mv.relative_path, modified = mv.modified
	FROM movedFiles mv
	WHERE arch.relative_path = mv.orginal_path;
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