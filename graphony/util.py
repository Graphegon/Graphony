from functools import wraps
from textwrap import dedent
from lazy_property import LazyWritableProperty as lazy

GxB_INDEX_MAX = 1 << 60


def _f_no_doc():
    pass


def _f_doc():
    " "
    pass


_no_codes = (_f_no_doc.__code__.co_code, _f_doc.__code__.co_code)


def query(f):
    d = dedent(f.__doc__.split("\n", 1)[1])
    doc_query = (
        "\n".join(line for line in d.split("\n") if line.startswith("    ")) or d
    )
    arg_count = doc_query.count("%s")
    code = True
    if f.__code__.co_code in _no_codes:
        code = False

    @wraps(f)
    def wrapper(self, cursor, *args, **kwargs):
        params = args[:arg_count]
        kw2 = kwargs.copy()
        kw2["self"] = self
        query = eval("""f'''""" + doc_query + """'''""", kw2)
        cursor.execute(query, params or None)
        r = f(self, cursor, *args[arg_count:], **kwargs)
        if code:
            return r
        else:
            return cursor.fetchone()[0]

    return wrapper


def curse(func):
    @wraps(func)
    def _decorator(self, *args, **kwargs):
        with self._graph._conn.cursor() as curs:
            r = func(self, curs, *args, **kwargs)
            # self.chain.logger.debug(curs.statusmessage)
            return r

    return _decorator
