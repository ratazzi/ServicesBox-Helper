CREATE TABLE IF NOT EXISTS `bundles` (
    "name" TEXT NOT NULL,
    "description" TEXT,
    PRIMARY KEY ("name")
);

CREATE TABLE IF NOT EXISTS `directories` (
    "id" INTEGER NOT NULL,
    "name" TEXT,
    "bundle" TEXT,
    "dir" TEXT,
    "permission" VARCHAR,
    "description" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS `options` (
    "id" INTEGER NOT NULL,
    "name" TEXT,
    "bundle" TEXT,
    "value" TEXT,
    "description" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS `services` (
    "id" INTEGER NOT NULL,
    "name" TEXT,
    "bundle" TEXT,
    "description" TEXT,
    "start" TEXT,
    "stop" TEXT,
    "restart" TEXT,
    "env" TEXT,
    "enable" INTEGER DEFAULT 1,
    "autostart" INTEGER DEFAULT 1,
    PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS `settings` (
    "id" INTEGER NOT NULL,
    "key" TEXT,
    "value" TEXT,
    PRIMARY KEY ("id")
);
