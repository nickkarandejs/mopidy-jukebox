BEGIN EXCLUSIVE TRANSACTION;

PRAGMA user_version = 1;                -- schema version

CREATE TABLE sources (
    url             TEXT PRIMARY KEY,   -- source URL
	successful      INTEGER, -- 0/1 successful last check
	last_check_time INTEGER  -- seconds since Unix epoch
);

END TRANSACTION;
