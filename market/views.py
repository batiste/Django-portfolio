# Create your views here.
from django import http
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.models import User
from market.models import Stock, Operation, Portfolio, PortfolioStock, StockAnalysis, convert_number
from market.authenticate import create_user
from django.template.context_processors import csrf
from yahoofinancials import YahooFinancials
import datetime
import numpy
import math
from django.urls import reverse


def check_ownership(request, portfolio=None, pstock=None):
    if portfolio and portfolio.owner != request.user:
        raise http.Http404

    if pstock and pstock.portfolio.owner != request.user:
        raise http.Http404


def index(request):

    portfolio_name = request.POST.get('portfolio_name', None)
    initial_cash = request.POST.get('initial_cash', 0)
    if portfolio_name:

        if not request.user.is_authenticated:
            user = create_user()
            authenticate(user=user)
            django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        p = Portfolio.objects.create(name=portfolio_name,
            owner=request.user, cash=initial_cash, initial_cash=initial_cash)
        url = reverse('portfolio', kwargs={'portfolio_pk': p.pk})
        return http.HttpResponseRedirect(url)

    if request.user.is_authenticated:
        portfolios = Portfolio.objects.filter(owner=request.user)
    else:
        portfolios = []

    c = {
        'portfolios':portfolios,
        'authenticated':request.user.is_authenticated
    }
    c.update(csrf(request))

    return render_to_response('index.html', c)


def login(request):

    auth_failed = False
    email = ""
    if request.method == 'POST' and request.POST.get('email'):
        email = request.POST.get('email')
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        authenticate(email=email, password=password)
        if user:
            django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return http.HttpResponseRedirect('..')
        else:
            auth_failed = True

    c = {
        'email':email,
        'auth_failed':auth_failed,
        'authenticated':request.user.is_authenticated
    }
    c.update(csrf(request))

    return render_to_response('login.html', c)


def logout(request):
    django_logout(request)
    return http.HttpResponseRedirect('..')


def manage_account(request):

    if not request.user.is_authenticated:
        user = create_user()
        authenticate(user=user)
        print(user)
        django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    else:
        user = request.user

    new_email = request.POST.get('new_email', None)
    new_password = request.POST.get('new_password', None)
    email_already_used = False
    email_updated = False

    if new_email and user.email != new_email:
        try:
            user = User.objects.get(email=new_email)
            email_already_used = True
        except User.DoesNotExist:
            pass

        if not email_already_used:
            user.email = new_email
            user.save()
            email_updated = True

    password_updated = False
    if new_password:
        user.set_password(new_password)
        user.save()
        password_updated = True

    c = {
        'password_updated':password_updated,
        'email_updated':email_updated,
        'user':user,
        'email_already_used':email_already_used,
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
        quote_name = quote_name.upper()
        yf = YahooFinancials(quote_name)
        exchange = yf.get_stock_exchange()
        try:
            stock = Stock.objects.get(name=quote_name)
        except Stock.DoesNotExist:
            stock = Stock.objects.create(
                name=quote_name,
                stock_exchange=yf.get_stock_exchange(),
                market_cap=convert_number(yf.get_market_cap()),
                last_price=convert_number(yf.get_current_price())
            )
            PortfolioStock.objects.get_or_create(stock=stock,
                portfolio=portfolio)

    stocks = PortfolioStock.objects.filter(portfolio=portfolio).order_by("-stock__value_score")

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
        yf = YahooFinancials(quote_name)
        stock.last_price = convert_number(yf.get_current_price())
        stock.price_sales_ratio = convert_number(yf.get_price_to_sales())
        stock.dividend_yield = convert_number(yf.get_dividend_yield())

        stock.save()
    return http.HttpResponseRedirect('..')


def update_shares(request, portfolio_pk):

    portfolio = Portfolio.objects.get(pk=portfolio_pk)
    check_ownership(request, portfolio)
    pstocks = PortfolioStock.objects.filter(portfolio=portfolio)
    for pstock in pstocks:
        analyze_stock(pstock)
    return http.HttpResponseRedirect('..')


def analyze_stock_view(request, portfolio_pk, portfolio_stock_pk):

    pstock = PortfolioStock.objects.get(pk=portfolio_stock_pk)
    check_ownership(request, pstock.portfolio)

    c = analyze_stock(pstock)

    return render_to_response('analysis.html', c)


def analyze_stock(pstock):

    days = 1000
    now = datetime.datetime.now()
    year_before = now - datetime.timedelta(days=days)

    stock = pstock.stock
    yf = YahooFinancials(stock.name)
    stock_analysis = StockAnalysis(yf)

    # update important fields
    stock.last_price = convert_number(yf.get_current_price())
    stock.price_sales_ratio = convert_number(yf.get_price_to_sales())
    stock.dividend_yield = convert_number(yf.get_annual_avg_div_yield())

    # historical_prices = yf.get_historical_price_data(stock.name,
    #     year_before.strftime('%Y%m%d'), now.strftime('%Y%m%d'), 'daily')

    #[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Clos']
    # history = []
    # historical_prices = historical_prices[1:]
    # has_history = True
    # for p in historical_prices:
    #     # error index out of range here
    #     if(len(p) == 1):
    #         has_history = False
    #         break
    #     close_v = float(p[4])
    #     date = datetime.datetime.strptime(p[0],'%Y-%m-%d')
    #     history.append({"date":date, "close_value":close_v})

    # price_trends = []
    # volatilities = [
    #     {'days':100},
    #     {'days':300},
    #     {'days':600},
    # ]
    # if has_history:
    #     # today first
    #     history = sorted(history, key=lambda p: p['date'])
    #     assert history[1]['date'] > history[0]['date']

    #     for v in volatilities:
    #         if len(history) < v['days']:
    #             v['days'] = len(history)

    #         v['volatility'] = round(calculate_historical_volatility(history[-v['days']:]), 2)
    #         v['start_date'] = history[-v['days']:][0]['date']

    #     stock_analysis.volatility = volatilities[1]['volatility']
    #     stock.volatility = stock_analysis.volatility

    #     start = 0
    #     interval = int(len(history) / 5.0)
    #     while len(history) > (start + interval) and interval > 0:
    #         trend = calculate_historical_price_trend(history[start:start+interval])
    #         price_trends.append(trend)
    #         start = start + interval
    #         #if len(history) < (start + interval):
    #         #    interval = len(history) - start - 1

    #     trend = calculate_historical_price_trend(history)
    #     price_trends.append(trend)
    #     stock_analysis.trend = trend

    stock.value_score = stock_analysis.value_score_analysis()
    stock.save()

    return {
        #'price_trends':price_trends,
        'stock':stock,
        #'volatilities':volatilities,
        'stock_analysis':stock_analysis,
        'days':days,
        #'history': history
    }


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


def calculate_historical_price_trend(history):

    start_date = history[0]['date']
    start_price = history[0]['close_value']
    # we go backward in time
    history = sorted(history, key=lambda p: p['date'], reverse=True)
    end_date = history[0]['date']
    end_price = history[0]['close_value']

    today = history[0]['close_value']
    gain = round((100 * (today - start_price)) / float(start_price), 2)

    year_average_change = round(gain / len(history) * 252, 2)

    return {
        'gain':gain,
        'days':len(history),
        'start_price':start_price,
        'end_price':end_price,
        'start_date': start_date,
        'end_date': end_date,
        'year_average_change': year_average_change
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
            raise ValueError("You cannot buy more that you can afford %d > %d" % (amount, portfolio.cash))

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


