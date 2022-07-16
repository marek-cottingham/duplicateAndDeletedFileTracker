DROP TABLE IF EXISTS currentFiles CASCADE;
DROP TABLE IF EXISTS archiveFiles CASCADE;
DROP TABLE IF EXISTS archiveDeletedFiles CASCADE;

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

CREATE TABLE archiveDeletedFiles (
	file_id BIGSERIAL NOT NULL PRIMARY KEY,
	relative_path VARCHAR NOT NULL,
	file_hash CHAR(64),
	modified TIMESTAMP(0),
	deleteDetected TIMESTAMP(0)
);