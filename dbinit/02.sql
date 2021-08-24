
BEGIN;

CREATE TABLE graphony.karate(
    s_id integer,
    d_id integer
    );

COPY graphony.karate FROM '/docker-entrypoint-initdb.d/karate.mtx' (DELIMITER ' ');
    
COMMIT;
