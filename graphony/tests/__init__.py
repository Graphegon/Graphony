import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import postgresql
from time import sleep

pgdata = TemporaryDirectory().name


def setup(pgdata=pgdata, log="db_test.log"):
    log = Path(log)
    log.unlink(True)
    postgresql.initdb(f"-D {pgdata} --auth-local=trust --no-sync -U postgres")
    postgresql.pg_ctl(f'-D {pgdata} -o "-k {pgdata} -h \\"\\"" -l {log} start')
    sleep(3)
    con_str = f"host={pgdata} user=postgres"
    postgresql.psql(f' -d "{con_str}" -f dbinit/01.sql -f dbinit/02.sql')
    return con_str


def teardown(pgdata=pgdata):
    msg = postgresql.pg_ctl(f"-D {pgdata} stop")
    shutil.rmtree(pgdata)
    return msg
