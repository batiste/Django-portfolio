from django.conf.urls import url, include
from market import views

urlpatterns = [
    url(r'^(?P<portfolio_pk>[0-9]*)/$', views.portfolio, name="portfolio"),
    url(r'^(?P<portfolio_pk>[0-9]*)/buy/(?P<portfolio_stock_pk>[\w]*)/$', views.operation, {'operation_type':'buy'}, name="portfolio_buy"),
    url(r'^(?P<portfolio_pk>[0-9]*)/sell/(?P<portfolio_stock_pk>[\w]*)/$', views.operation, {'operation_type':'sell'}, name="portfolio_sell"),
    url(r'^(?P<portfolio_pk>[0-9]*)/remove/(?P<portfolio_stock_pk>[\w]*)/$', views.remove_stock, name="portfolio_remove_stock"),
    url(r'^(?P<portfolio_pk>[0-9]*)/update_shares/$', views.update_shares, name="portfolio_update_shares"),
    url(r'^(?P<portfolio_pk>[0-9]*)/analyse/(?P<portfolio_stock_pk>[\w]*)/$', views.analyze_stock_view, name="portfolio_analyse_stock"),
    url(r'account/$', views.manage_account, name="portfolio_account"),
    url(r'login/$', views.login, name="portfolio_login"),
    url(r'logout/$', views.logout, name="portfolio_logout"),
    url(r'^$', views.index, name="portfolio_index"),
]