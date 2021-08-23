BEGIN;

CREATE SCHEMA graphony;

CREATE TABLE graphony.node(
    n_id BIGSERIAL,
    n_name TEXT NOT NULL,
    n_props JSONB,
    UNIQUE (n_name) INCLUDE (n_id),
    PRIMARY KEY (n_id) INCLUDE (n_name)
    );

CREATE TABLE graphony.relation(
    r_id BIGSERIAL,
    r_name TEXT NOT NULL,
    UNIQUE (r_name) INCLUDE (r_id),
    PRIMARY KEY (r_id) INCLUDE (r_name)
    );

CREATE TABLE graphony.edge(
    e_id BIGSERIAL PRIMARY KEY,
    r_id BIGINT REFERENCES graphony.relation(r_id),
    e_props JSONB
    );

COMMIT;
