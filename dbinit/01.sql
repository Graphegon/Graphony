BEGIN;

CREATE SCHEMA graphony;

CREATE TABLE graphony.hyperspace(
    id BIGSERIAL
    );

CREATE TABLE graphony.node(
    n_name TEXT NOT NULL,
    n_props JSONB,
    UNIQUE (n_name) INCLUDE (id),
    PRIMARY KEY (id) INCLUDE (n_name)
    ) INHERITS (graphony.hyperspace);

CREATE TABLE graphony.relation(
    r_name TEXT NOT NULL,
    r_type BYTEA NOT NULL,
    UNIQUE (r_name) INCLUDE (id),
    PRIMARY KEY (id) INCLUDE (r_name)
    ) INHERITS (graphony.hyperspace);

CREATE INDEX ON graphony.relation (r_type);

CREATE TABLE graphony.edge(
    e_props JSONB,
    PRIMARY KEY (id)
    ) INHERITS (graphony.hyperspace);

COMMIT;
