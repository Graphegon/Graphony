from functools import wraps
from textwrap import dedent

GxB_INDEX_MAX = 1 << 60


def _f_no_doc():
    pass


def _f_doc():
    " "


_no_codes = (_f_no_doc.__code__.co_code, _f_doc.__code__.co_code)


def curse(func):
    @wraps(func)
    def _decorator(self, *args, **kwargs):
        with self.graph._conn.cursor() as curs:
            r = func(self, curs, *args, **kwargs)
            # self.chain.logger.debug(curs.statusmessage)
            return r

    return _decorator


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
        _query = eval("""f'''""" + doc_query + """'''""", kw2)  # noqa
        cursor.execute(_query, params or None)
        r = f(self, cursor, *args[arg_count:], **kwargs)
        if code:
            return r

        r = cursor.fetchone()
        if r is not None:
            r = r[0]
        return r

    return curse(wrapper)
