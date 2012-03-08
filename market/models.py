from django.db import models
from django.contrib.auth.models import User
import math


def millify(n):
    # n==0 create an error
    if n < 100:
        return n
    millnames=['','T','M','B','T']
    millidx=max(0,min(len(millnames)-1,
                      int(math.floor(math.log10(abs(n))/3.0))))
    return '%.2f %s'%(n/10**(3*millidx), millnames[millidx])

def convert_number(number):
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

        profit = total_value - total_spent
        return total_value, total_spent, profit


class Stock(models.Model):

    name = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150,
        blank=True)

    stock_exchange = models.CharField(max_length=150,
        blank=True)

    market_cap = models.FloatField()
    last_price = models.FloatField()

    # value measures
    price_sales_ratio = models.FloatField(default=0)
    dividend_yield = models.FloatField(default=0)

    #volatility = models.FloatField(null=True)

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
        current_value = total_amount * self.stock.last_price

        profit = current_value - money_spent

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
    """
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
        self.psr = convert_number(infos['price_sales_ratio'])
        self.dividend_yield = convert_number(infos['dividend_yield'])
        self.price_earnings_growth_ratio = convert_number(infos['price_earnings_growth_ratio'])

        self.price = convert_number(infos['price'])
        self.high_52 = convert_number(infos['52_week_high'])
        self.low_52 = convert_number(infos['52_week_low'])

    def price_52_bar(self):

        max_value = self.high_52 - self.low_52
        current_value = self.price - self.low_52
        percent_low = int(current_value / max_value * 100)
        return percent_low

    def cap_display(self):
        return millify(self.cap)

    def company_cap_type(self):
        if self.cap < 200000000:
            return "Small"
        if self.cap < 1000000000:
            return "Middle"
        if self.cap < 5000000000:
            return "Large"
        return "Very large"

    def price_earnings_ratio_type(self):
        if self.per < 6:
            return "Low market confidence"
        if self.per > 100:
            return "Extremly high market confidence"
        if self.per > 50:
            return "Very high market confidence"
        if self.per > 20:
            return "High market confidence"
        if self.per > 12:
            return "Strong market confidence"

        return "Average market confidence"

    def growth_type(self):

        if self.price_earnings_growth_ratio < 0.6:
            return "Undervalued"

        if self.price_earnings_growth_ratio < 0.8:
            return "Possibly undervalued"

        if self.price_earnings_growth_ratio > 2:
            return "Possibly overvalued"

        return "-"

    def dividend_type(self):
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
        if self.psr < 1.5:
            return "Low price"

        if self.psr > 2:
            return "High price"

        return "Middle"