from pygraphblas import Vector, FP64
from pygraphblas.descriptor import S


def pagerank(A, damping=0.85, itermax=100, tol=1e-4):
    T = A.type
    d_out = A.reduce()
    n = d_out.nvals
    t = Vector.sparse(T, fill=0, mask=d_out)
    r = Vector.sparse(T, fill=1.0 / n, mask=d_out)
    dmin = Vector.sparse(T, fill=1.0 / damping, mask=d_out)
    d = d_out / damping
    d.eadd(dmin, T.max, out=d)
    teleport = (1 - damping) / n

    breakpoint()
    for i in range(1, itermax):
        t, r = r, t
        w = t / d
        r[t] = teleport
        A.plus_second(w, out=r, accum=T.plus)
        t -= r
        t.abs(out=t)
        if t.reduce_float() <= tol:
            break
    return r, i
