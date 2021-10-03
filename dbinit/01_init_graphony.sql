BEGIN;

CREATE SCHEMA graphony;

CREATE TABLE graphony.hyperspace(
    id BIGSERIAL,
    name TEXT,
    props JSONB
    );

CREATE TABLE graphony.node(
    PRIMARY KEY (id) INCLUDE (name),
    UNIQUE (name) INCLUDE (id)
    ) INHERITS (graphony.hyperspace);

CREATE TABLE graphony.relation(
    pytype BYTEA NOT NULL,
    UNIQUE (name) INCLUDE (id),
    PRIMARY KEY (id) INCLUDE (name)
    ) INHERITS (graphony.hyperspace);

CREATE TABLE graphony.edge(
    PRIMARY KEY (id)
    ) INHERITS (graphony.hyperspace);

COMMIT;
