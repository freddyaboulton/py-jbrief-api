-- upgrade --
CREATE TABLE IF NOT EXISTS "contestants" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "occupation" TEXT NOT NULL,
    "city" TEXT NOT NULL,
    "state" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "questions" (
    "id" VARCHAR(32) NOT NULL  PRIMARY KEY,
    "text" TEXT NOT NULL,
    "answer" TEXT NOT NULL,
    "category" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "turns" (
    "id" VARCHAR(32) NOT NULL  PRIMARY KEY,
    "game_id" INT NOT NULL,
    "order" INT NOT NULL,
    "change_in_score" REAL NOT NULL,
    "is_daily_double" INT NOT NULL,
    "is_final_jeopardy" INT NOT NULL,
    "contestant_id" INT NOT NULL REFERENCES "contestants" ("id") ON DELETE CASCADE,
    "question_id" VARCHAR(32) NOT NULL REFERENCES "questions" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
