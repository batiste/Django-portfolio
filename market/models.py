from django.db import models
from django.contrib.auth.models import User
import math

def normalize(neutral_point, value, bigger_better=True, limits=[]):

    if limits:
        if value < limits[0]:
            value = limits[0]
        if value > limits[1]:
            value = limits[1]

    if bigger_better:
        return value - neutral_point
    else:
        return neutral_point - value


def millify(n):
    # n==0 create an error
    if n < 100:
        return n
    millnames=['','T','M','B','T']
    millidx=max(0,min(len(millnames)-1,
                      int(math.floor(math.log10(abs(n))/3.0))))
    return '%.2f %s'%(n/10**(3*millidx), millnames[millidx])

def convert_number(number):

    if number == "N/A":
        return None

    number = number.lower()
    if number.endswith('b'):
        number = float(number[:-1])
        number = number * 1000000000
        return number

    if number.endswith('m'):
        number = float(number[:-1])
        number = number * 1000000
        return number

    try:
        return float(number)
    except:
        return 0
    return 0


class Portfolio(models.Model):

    name = models.CharField(max_length=150, unique=True)
    owner = models.ForeignKey(User)
    initial_cash = models.FloatField(default=0)
    cash = models.FloatField(default=0)

    def balance_sheet(self):
        total_value = 0
        total_spent = 0
        stocks = PortfolioStock.objects.filter(portfolio=self)
        for s in stocks:
            total_value += s.current_value()
            total_spent += s.money_spent()

        profit = round(total_value - total_spent, 2)
        return total_value, total_spent, profit

    def profit_percent(self):
        total_value, total_spent, profit = self.balance_sheet()
        if total_spent <= 0:
            return 0
        return round(profit / total_spent * 100, 2)


class Stock(models.Model):

    name = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150,
        blank=True)

    stock_exchange = models.CharField(max_length=150,
        blank=True)

    market_cap = models.FloatField(default=0, null=True)
    last_price = models.FloatField(default=0, null=True)

    # value measures
    price_sales_ratio = models.FloatField(default=0, null=True)
    dividend_yield = models.FloatField(default=0, null=True)

    volatility = models.FloatField(null=True)
    value_score = models.FloatField(null=True)

    def shares(self):
        if self.last_price != 0:
            return millify(self.market_cap / self.last_price)
        return 0

    def cap(self):
        return millify(self.market_cap)

    def price(self):
        return millify(self.last_price)


class PortfolioStock(models.Model):
    """
    A stock within a portfolio.
    """

    portfolio = models.ForeignKey(Portfolio)
    stock = models.ForeignKey(Stock)

    class Meta:
        unique_together = (("portfolio", "stock"),)

    def price():
        return self.stock.last_price

    def holding(self):
        operations = Operation.objects.filter(portfolio_stock=self)
        total_amount = 0
        money_spent = 0
        for op in operations:
            total_amount += op.amount
            money_spent += op.amount * op.price
        if self.stock.last_price is not None:
            current_value = total_amount * self.stock.last_price
        else:
            current_value = 0

        profit = round(current_value - money_spent, 2)

        return total_amount, money_spent, current_value, profit

    def shares_owned(self):
        return self.holding()[0]

    def money_spent(self):
        return self.holding()[1]

    def current_value(self):
        return self.holding()[2]

    def profit(self):
        return self.holding()[3]


class Operation(models.Model):
    """django round

    Buy or sell of a stock
    """

    amount = models.FloatField()
    price = models.FloatField()
    time = models.DateTimeField(auto_now=True)
    portfolio_stock = models.ForeignKey(PortfolioStock)

    class Meta:
        ordering = ['-time']

    def value(self):
        return self.amount * self.price

    def diff_cash(self):
        return - self.amount * self.price

    def __unicode__(self):
        op_type = ""
        if self.amount > 0:
            op_type = "Buy"
        if self.amount < 0:
            op_type =  "Sell"
        return op_type + ' ' + self.portfolio_stock.stock.name


class StockValue(models.Model):
    """
    Historic sotck value (Not used yet)
    """

    value = models.FloatField()
    time = models.DateTimeField(auto_now=True)
    stock = models.ForeignKey(Stock)


class StockAnalysis(object):

    def __init__(self, infos):
        self.cap = convert_number(infos['market_cap'])
        self.per = convert_number(infos['price_earnings_ratio'])
        self.price_sales_ratio = convert_number(infos['price_sales_ratio'])
        self.ebitda = convert_number(infos['ebitda'])
        self.dividend_yield = convert_number(infos['dividend_yield'])
        self.price_earnings_growth_ratio = convert_number(infos['price_earnings_growth_ratio'])

        self.volatility = None
        self.price = convert_number(infos['price'])
        self.high_52 = convert_number(infos['52_week_high'])
        self.low_52 = convert_number(infos['52_week_low'])
        self.trend = None

        self.price_book_ratio = convert_number(infos['price_book_ratio'])

        self.value_score = 0
        self.growth_score = 0

    def value_score_analysis(self):

        value_score = 0

        if self.price_book_ratio is not None:
            value_score += normalize(1.5, math.sqrt(self.price_book_ratio),
                bigger_better=False, limits=[0, 1000])

        # price / earnings is an important ratio
        if self.per is not None:
            value_score += 100.0 / self.per

        # low volatility is preferable
        if self.volatility is not None:
            value_score += normalize(50, self.volatility,
                bigger_better=False, limits=[0, 1000]) / 10.0

        # could it be an opportunity on 52 weeks ?
        if self.price_52_percent() is not None:
            value_score += normalize(50, self.price_52_percent(),
                bigger_better=False, limits=[0, 100]) / 40.0

        # PEG Ratio of 2 to 3 is considered OK. A PEG Ratio above 3 usually
        # means that the company's stock is over priced
        if self.price_earnings_growth_ratio is not None:
            value_score += normalize(2.5, self.price_earnings_growth_ratio,
                bigger_better=False, limits=[0, 100])


        if self.dividend_yield is not None:
            # dividend yield is a important factor
            # for large company
            if self.cap > 1000000000:
                value_score += self.dividend_yield * 1.5
            else:
                value_score += self.dividend_yield

        if self.price_sales_ratio is not None:
            # price to sales is an important factor
            value_score += normalize(1.5, self.price_sales_ratio,
                bigger_better=False, limits=[0, 100]) * 2

        if self.trend is not None:
            # the past cannot predict the future: 100% growth == 5 points
            value_score += normalize(0, self.trend['year_average_change'],
                bigger_better=True) / 20.0

        self.value_score = value_score

        return value_score

    def price_book_ratio_analysis(self):
        if self.price_book_ratio is None:
             return "-"

        if self.price_book_ratio < 1:
            return "Very good"

        if self.price_book_ratio < 2:
            return "Good"

        if self.price_book_ratio > 8:
            return "Very high"

        if self.price_book_ratio > 5:
            return "High"

        return "-"

    def volatility_analysis(self):

        if self.volatility < 15:
            return "%.2f%% is a very low volatility value" % self.volatility

        if self.volatility < 20:
            return "%.2f%% is a low volatility value" % self.volatility

        if self.volatility > 25:
            return "%.2f%% is a high volatility value" % self.volatility

        return "%.2f%% is an average volatility value" % self.volatility


    def price_52_percent(self):
        if self.high_52 is None or self.low_52 is None:
            return 50
        max_value = self.high_52 - self.low_52
        if max_value == 0:
            return None
        current_value = self.price - self.low_52

        percent_low = int(current_value / max_value * 100)
        return percent_low

    def cap_display(self):
        return millify(self.cap)

    def company_cap_analysis(self):
        if self.cap is None:
             return "-"

        if self.cap < 200000000:
            return "Small"
        if self.cap < 1000000000:
            return "Middle"
        if self.cap < 5000000000:
            return "Large"
        return "Very large"

    def price_earnings_ratio_analysis(self):

        if self.per is None:
             return "-"

        if self.per < 16:
            return "Very good"
        if self.per < 25:
            return "Good"
        if self.per > 30:
            return "High"

        return "-"

    def growth_analysis(self):
        if self.price_earnings_growth_ratio is None:
             return "-"

        if self.price_earnings_growth_ratio < 2:
            return "Good"

        if self.price_earnings_growth_ratio > 3:
            return "Over priced"

        return "-"

    def dividend_analysis(self):
        if self.dividend_yield is None:
             return "-"

        if self.dividend_yield > 6:
            return "Very high"
        if self.dividend_yield > 3:
            return "High"
        if self.dividend_yield >= 2:
            return "Average"
        if self.dividend_yield < 2:
            return "Low"
        return "N/A"

        return "Average market confidence"

    def price_to_sales(self):
        if self.price_sales_ratio is None:
             return "-"

        if self.price_sales_ratio < 1.5:
            return "Low price"

        if self.price_sales_ratio > 5:
            return "High price"

        return "-"