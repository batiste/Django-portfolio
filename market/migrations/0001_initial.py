# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Portfolio'
        db.create_table('market_portfolio', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=150)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('initial_cash', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('cash', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal('market', ['Portfolio'])

        # Adding model 'Stock'
        db.create_table('market_stock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('stock_exchange', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('market_cap', self.gf('django.db.models.fields.FloatField')()),
            ('last_price', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('market', ['Stock'])

        # Adding model 'PortfolioStock'
        db.create_table('market_portfoliostock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('portfolio', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['market.Portfolio'])),
            ('stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['market.Stock'])),
        ))
        db.send_create_signal('market', ['PortfolioStock'])

        # Adding unique constraint on 'PortfolioStock', fields ['portfolio', 'stock']
        db.create_unique('market_portfoliostock', ['portfolio_id', 'stock_id'])

        # Adding model 'Operation'
        db.create_table('market_operation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('amount', self.gf('django.db.models.fields.FloatField')()),
            ('price', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('portfolio_stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['market.PortfolioStock'])),
        ))
        db.send_create_signal('market', ['Operation'])

        # Adding model 'StockValue'
        db.create_table('market_stockvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['market.Stock'])),
        ))
        db.send_create_signal('market', ['StockValue'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'PortfolioStock', fields ['portfolio', 'stock']
        db.delete_unique('market_portfoliostock', ['portfolio_id', 'stock_id'])

        # Deleting model 'Portfolio'
        db.delete_table('market_portfolio')

        # Deleting model 'Stock'
        db.delete_table('market_stock')

        # Deleting model 'PortfolioStock'
        db.delete_table('market_portfoliostock')

        # Deleting model 'Operation'
        db.delete_table('market_operation')

        # Deleting model 'StockValue'
        db.delete_table('market_stockvalue')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'market.operation': {
            'Meta': {'ordering': "['-time']", 'object_name': 'Operation'},
            'amount': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'portfolio_stock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.PortfolioStock']"}),
            'price': ('django.db.models.fields.FloatField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'market.portfolio': {
            'Meta': {'object_name': 'Portfolio'},
            'cash': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_cash': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'market.portfoliostock': {
            'Meta': {'unique_together': "(('portfolio', 'stock'),)", 'object_name': 'PortfolioStock'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'portfolio': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Portfolio']"}),
            'stock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Stock']"})
        },
        'market.stock': {
            'Meta': {'object_name': 'Stock'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_price': ('django.db.models.fields.FloatField', [], {}),
            'market_cap': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'stock_exchange': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'})
        },
        'market.stockvalue': {
            'Meta': {'object_name': 'StockValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Stock']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        }
    }

    complete_apps = ['market']
