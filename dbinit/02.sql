
BEGIN;

CREATE TABLE graphony.karate(
    s_id integer,
    d_id integer
    );

\COPY graphony.karate FROM 'dbinit/karate.mtx' (DELIMITER ' ');
    
COMMIT;
