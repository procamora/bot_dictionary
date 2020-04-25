BEGIN TRANSACTION;
DROP TABLE IF EXISTS "Words";
CREATE TABLE IF NOT EXISTS "Words"
(
    "id"      INTEGER NOT NULL UNIQUE,
    "english" TEXT    NOT NULL UNIQUE,
    "spanish" TEXT    NOT NULL,
    PRIMARY KEY ("id")
);


DROP TABLE IF EXISTS "Stats";
CREATE TABLE IF NOT EXISTS "Stats"
(
    "id"         INTEGER NOT NULL UNIQUE,
    "id_user"    INTEGER NOT NULL,
    "id_word"    INTEGER NOT NULL,
    "successful" TEXT    NOT NULL,
    PRIMARY KEY ("id")
);
COMMIT;
