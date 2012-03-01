import operator
import warnings

from . import impl
from .impl import get as get_all


# FIXME: metaprogram evilness
for field in impl._FIELDS:
    # 'Simpler' implementation has wonky closure shadowing
    #func = lambda symbol: get_all(symbol)[field]
    # DOUBLE YOU TEE EFF: http://lackingrhoticity.blogspot.com/2009/04/python-variable-binding-semantics-part.html#c5923214396394060839
    func = (lambda field: lambda symbol: get_all(symbol)[field].strip('"'))(field)
    func.__name__ = 'get_' + field
    locals()[func.__name__] = func
