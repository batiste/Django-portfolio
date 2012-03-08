# Create your views here.
from django import http
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login
from market.models import Stock, Operation, Portfolio, PortfolioStock, StockAnalysis, convert_number
from market.authenticate import create_user
from django.core.context_processors import csrf
import ystockquote
import datetime
import numpy
import math


def check_ownership(request, portfolio=None, pstock=None):
    if portfolio and portfolio.owner != request.user:
        raise http.Http404

    if pstock and pstock.portfolio.owner != request.user:
        raise http.Http404


def index(request):

    portfolio_name = request.POST.get('portfolio_name', None)
    initial_cash = request.POST.get('initial_cash', 0)
    if portfolio_name:

        if not request.user.is_authenticated():
            user = create_user()
            user = authenticate(user=user)
            login(request, user)

        p = Portfolio.objects.create(name=portfolio_name,
            owner=request.user, cash=initial_cash, initial_cash=initial_cash)
        return http.HttpResponseRedirect('/portfolio/%d/' % p.pk)

    if request.user.is_authenticated():
        portfolios = Portfolio.objects.filter(owner=request.user)
    else:
        portfolios = []

    c = {
        'portfolios':portfolios,
        'authenticated':request.user.is_authenticated()
    }
    c.update(csrf(request))

    return render_to_response('index.html', c)


def manage_account(request):

    if not request.user.is_authenticated():
        user = create_user()
        user = authenticate(user=user)
        login(request, user)
    else:
        user = request.user

    new_email = request.POST.get('new_email', None)
    if new_email:
        user.email = new_email
        user.save()

    c = {
        'user':user,
        'email':user.email
    }
    c.update(csrf(request))

    return render_to_response('account.html', c)


def portfolio(request, portfolio_pk):

    portfolio = Portfolio.objects.get(pk=portfolio_pk)
    check_ownership(request, portfolio)
    stock_not_found = False

    quote_name = request.POST.get('quote', None)
    if quote_name:
        answer = ystockquote.get(quote_name)
        if answer["stock_exchange"] != '"N/A"':
            try:
                stock = Stock.objects.get(name=quote_name)
            except Stock.DoesNotExist:
                stock = Stock.objects.create(
                    name=quote_name,
                    stock_exchange=answer['stock_exchange'],
                    market_cap=convert_number(answer['market_cap']),
                    last_price=convert_number(answer['price'])
                )
            PortfolioStock.objects.get_or_create(stock=stock,
                portfolio=portfolio)
        else:
            stock_not_found = True

    stocks = PortfolioStock.objects.filter(portfolio=portfolio)

    operations = Operation.objects.filter(portfolio_stock__portfolio=portfolio)[0:10]

    total_value, total_spent, profit = portfolio.balance_sheet()
    if total_spent != 0:
        profit_purcent = round(profit / total_spent * 100, 2)
    else:
        profit_purcent = 0

    total_cash_value = total_value + portfolio.cash

    c = {
        'quote_name': quote_name,
        'stock_not_found': stock_not_found,
        'portfolio':portfolio,
        'stocks': stocks,
        'operations':operations,
        'total_value':total_value,
        'total_spent':total_spent,
        'profit':profit,
        'profit_purcent':profit_purcent,
        'total_cash_value':total_cash_value,
    }
    c.update(csrf(request))

    return render_to_response('portfolio.html', c)


def update_shares(request, portfolio_pk):

    portfolio = Portfolio.objects.get(pk=portfolio_pk)
    check_ownership(request, portfolio)
    pstocks = PortfolioStock.objects.filter(portfolio=portfolio)
    for pstock in pstocks:
        stock = pstock.stock
        answer = ystockquote.get(stock.name)
        stock.last_price = convert_number(answer['price'])

        stock.price_sales_ratio = convert_number(answer['price_sales_ratio'])
        stock.dividend_yield = convert_number(answer['dividend_yield'])

        stock.save()
    return http.HttpResponseRedirect('..')



def analyze_stock(request, portfolio_pk, portfolio_stock_pk):

    pstock = PortfolioStock.objects.get(pk=portfolio_stock_pk)
    check_ownership(request, pstock.portfolio)

    days = 1000
    now = datetime.datetime.now()
    year_before = now - datetime.timedelta(days=days)

    stock = pstock.stock
    infos = ystockquote.get(stock.name)
    print infos
    stock_analysis = StockAnalysis(infos)

    historical_prices = ystockquote.legacy.get_historical_prices(stock.name,
        year_before.strftime('%Y%m%d'), now.strftime('%Y%m%d'))

    #[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Clos']
    history = []
    historical_prices = historical_prices[1:]
    for p in historical_prices:
        close_v = float(p[4])
        date = datetime.datetime.strptime(p[0],'%Y-%m-%d')
        history.append({"date":date, "close_value":close_v})

    history = sorted(history, key=lambda p: p['date'])
    assert history[1]['date'] > history[0]['date']

    volatilities = [
        {'days':100},
        {'days':300},
        {'days':600},
    ]

    for v in volatilities:
        if len(history) < v['days']:
            v['days'] = len(history)

        v['volatility'] = round(calculate_historical_volatility(history[-v['days']:]), 2)
        v['start_date'] = history[-v['days']:][0]['date']

    current_v = volatilities[-1:]

    price_trends = [
        {'days':50, 'interval':2},
        {'days':100, 'interval':10},
        {'days':300, 'interval':20},
        {'days':600, 'interval':30},
    ]
    for p in price_trends:
        if len(history) < p['days']:
            p['days'] = len(history)
        trend = calculate_historical_price_trend(history[-p['days']:], interval=p['interval'])
        p.update(trend)
        p['start_date'] = history[-p['days']:][0]['date']

    c = {
        'price_trends':price_trends,
        'stock':stock,
        'infos':infos,
        'volatilities':volatilities,
        'stock_analysis':stock_analysis,
        'days':days,
        'history': history
    }
    return render_to_response('analysis.html', c)


def calculate_historical_volatility(history):
    # http://www.investopedia.com/university/optionvolatility/volatility2.asp
    last_close_value = None
    purcent_list = []
    for p in history:
        if last_close_value is not None:
            purcent_change = (p['close_value'] - last_close_value) / last_close_value * 100
            purcent_list.append(purcent_change)
        last_close_value = p['close_value']

    std = numpy.std(purcent_list)
    return std * math.sqrt(len(history))


def calculate_historical_price_trend(history, interval=50):

    # we go backward
    history = sorted(history, key=lambda p: p['date'], reverse=True)

    last_close_value = history[0]['close_value']

    up_trend_acc = 0
    down_trend_acc = 0
    up = 0
    down = 0
    i = 0

    for p in history:
        i = i + 1
        if i >= interval:
            i = 0
            if p['close_value'] < last_close_value:
                up_trend_acc += last_close_value - p['close_value']
                up += 1
            elif p['close_value'] > last_close_value:
                down_trend_acc += p['close_value'] - last_close_value
                down += 1
            last_close_value = p['close_value']

    up_percent = float(up) / (up + down) * 100
    total_mouvement = float(down_trend_acc + up_trend_acc)
    today = history[0]['close_value']
    start = history[len(history)-1]['close_value']
    gain = round((100 * (today - start)) / float(start), 2)

    return {
        'up_percent':round(up_percent, 1),
        'mouvement_gain':round(100 * up_trend_acc / total_mouvement, 1),
        'mouvement_loss':round(100 * down_trend_acc / total_mouvement, 1),
        'gain':gain
    }


def operation(request, portfolio_pk, portfolio_stock_pk, operation_type):

    portfolio = Portfolio.objects.get(pk=portfolio_pk)
    pstock = PortfolioStock.objects.get(pk=portfolio_stock_pk)
    check_ownership(request, portfolio=portfolio, pstock=pstock)

    amount = request.POST.get('amount', None)
    confirmed = request.POST.get('confirm', None)
    confirm = False
    try:
        amount = int(amount)
        confirm = True
    except TypeError:
        amount = 0

    if amount < 0:
        raise ValueError("Negative value not allowed")

    if operation_type == 'sell':
        if amount > pstock.shares_owned():
            raise ValueError("You cannot sell more than you own")

    if operation_type == 'buy':
        if amount > portfolio.cash:
            raise ValueError("You cannot buy more that you can afford")

    if confirmed and amount:
        if operation_type == 'sell':
            amount = -amount

        operation = Operation.objects.create(portfolio_stock=pstock,
            price=pstock.stock.last_price, amount=amount)

        portfolio.cash = portfolio.cash - (amount * pstock.stock.last_price)
        portfolio.save()
        return http.HttpResponseRedirect('../..')

    total = amount * pstock.stock.last_price

    c = {'pstock': pstock,
        'confirm':confirm,
        'total': total,
        'operation_type':operation_type,
        'amount': amount}
    c.update(csrf(request))

    return render_to_response('buy.html', c)


def remove_stock(request, portfolio_pk, portfolio_stock_pk):

    portfolio = Portfolio.objects.get(pk=portfolio_pk)
    pstock = PortfolioStock.objects.get(pk=portfolio_stock_pk)
    check_ownership(request, portfolio, pstock)

    if pstock.shares_owned() != 0:
        raise ValueError("You cannot remove this stock")

    pstock.delete()

    return http.HttpResponseRedirect('../..')


