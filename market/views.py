# Create your views here.
from django import http
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login
from market.models import Stock, Operation, Portfolio, PortfolioStock
from market.authenticate import create_user
from django.core.context_processors import csrf
import ystockquote


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


def check_ownership(request, portfolio):
    if portfolio.owner != request.user:
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
        stock.save()
    return http.HttpResponseRedirect('..')


def operation(request, portfolio_pk, portfolio_stock_pk, operation_type):

    portfolio = Portfolio.objects.get(pk=portfolio_pk)
    check_ownership(request, portfolio)
    pstock = PortfolioStock.objects.get(pk=portfolio_stock_pk)

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
    check_ownership(request, portfolio)
    pstock = PortfolioStock.objects.get(pk=portfolio_stock_pk)

    if pstock.shares_owned() != 0:
        raise ValueError("You cannot remove this stock")

    pstock.delete()

    return http.HttpResponseRedirect('../..')


