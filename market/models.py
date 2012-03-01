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

    def shares(self):
        return millify(self.market_cap / self.last_price)

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