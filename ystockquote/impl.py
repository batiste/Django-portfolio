import operator

from . import legacy


_DIRECTIVES = [
    ('l1', 'price'),
    ('c1', 'change'),
    ('v' , 'volume'),
    ('a2', 'avg_daily_volume'),
    ('x' , 'stock_exchange'),
    ('j1', 'market_cap'),
    ('b4', 'book_value'),
    ('j4', 'ebitda'),
    ('d' , 'dividend_per_share'),
    ('y' , 'dividend_yield'),
    ('e' , 'earnings_per_share'),
    ('k' , '52_week_high'),
    ('j' , '52_week_low'),
    ('m3', '50day_moving_avg'),
    ('m4', '200day_moving_avg'),
    ('r' , 'price_earnings_ratio'),
    ('r5', 'price_earnings_growth_ratio'),
    ('p5', 'price_sales_ratio'),
    ('p6', 'price_book_ratio'),
    ('s7', 'short_ratio'),
]
_STATS = map(operator.itemgetter(0), _DIRECTIVES)
_FIELDS = map(operator.itemgetter(1), _DIRECTIVES)


def _get_no_cache(symbol):
    values = legacy.__request(symbol, ''.join(_STATS)).split(',')
    data = {}
    for (i, field) in enumerate(_FIELDS):
        data[field] = values[i]

    return data


def get(symbol, cache={}):
    if symbol not in cache:
        cache[symbol] = _get_no_cache(symbol)

    return cache[symbol]


