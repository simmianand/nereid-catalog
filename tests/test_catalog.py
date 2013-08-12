# -*- coding: utf-8 -*-
'''
    Catalog test suite

    :copyright: (c) 2010-2013 by Openlabs Technologies & Consulting (P) Ltd.
    :license: GPLv3, see LICENSE for more details

'''
import json
import unittest
from decimal import Decimal

from lxml import objectify

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT, \
    test_view, test_depends
from nereid.testing import NereidTestCase
from trytond.transaction import Transaction


class TestCatalog(NereidTestCase):
    """
    Test Catalog
    """

    def _create_product_category(self, name, vlist):
        """
        Creates a product category

        Name is mandatory while other value may be provided as keyword
        arguments

        :param name: Name of the product category
        """
        Category = POOL.get('product.category')
        print "vlist>>>>>>>>>>>", vlist

        for values in vlist:
            values['name'] = name
        print "vlist>>>>>>>>>>>>", vlist
        return Category.create(vlist)

    def _create_product_template(self, name, vlist, uom=u'Unit'):
        """
        Create a product and return its ID

        Additional arguments may be provided as keyword arguments

        :param name: Name of the product
        :param uom: Note it is the name of UOM (not symbol or code)
        """
        Template = POOL.get('product.template')
        Uom = POOL.get('product.uom')

        print "vlist>>>>>>>>>>>", vlist

        for values in vlist:
            values['name'] = name
            values['default_uom'], = Uom.search([('name', '=', uom)], limit=1)

        print "vlist?>>>>>>>>>>>", vlist

        return Template.create(vlist)

    def setup_defaults(self):
        """
        Setup the defaults
        """
        usd, = self.Currency.create([{
            'name': 'US Dollar',
            'code': 'USD',
            'symbol': '$',
        }])
        company_party, = self.Party.create([{
            'name': 'Openlabs',
        }])
        company, = self.Company.create([{
            'party': company_party.id,
            'currency': usd.id,
        }])
        party1, party2 = self.Party.create([{
            'name': 'Guest User',
        }, {
            'name': 'Registered User',
        }])
        guest_user, = self.NereidUser.create([{
            'party': party1.id,
            'display_name': 'Guest User',
            'email': 'guest@openlabs.co.in',
            'password': 'password',
            'company': company.id,
        }])
        self.registered_user = self.NereidUser.create([{
            'party': party2.id,
            'display_name': 'Registered User',
            'email': 'email@example.com',
            'password': 'password',
            'company': company.id,
        }])

        # Create product categories
        category, = self._create_product_category(
            'Category', [{'uri': 'category'}]
        )
        category2, = self._create_product_category(
            'Category 2', [{'uri': 'category2'}]
        )
        category3, = self._create_product_category(
            'Category 3', [{'uri': 'category3'}]
        )
        print ">>>>>>category.id>>>>>>", category.id
        print ">>>>category2.id>>>>>>>>", category2.id
        print ">>>>>>>>category3>>>>", category3.id

        # Create website
        url_map, = self.URLMap.search([], limit=1)
        en_us, = self.Language.search([('code', '=', 'en_US')])
        website, = self.NereidWebsite.create([{
            'name': 'localhost',
            'url_map': url_map.id,
            'company': company.id,
            'application_user': USER,
            'default_language': en_us.id,
            'guest_user': guest_user.id,
        }])

        self.NereidWebsite.write(
            [website], {
                'categories': [('set', [category.id, category2.id])],
                'currencies': [('set', [usd.id])],
            }
        )

        # Create Product Templates
        template1, = self.Template.create([{
            'name': 'product 1',
            'type': 'goods',
            'category': category.id,
            'list_price': Decimal('10'),
            'cost_price': Decimal('5'),
        }])
        template2, = self.Template.create([{
            'name': 'product 2',
            'type': 'goods',
            'category': category2.id,
            'list_price': Decimal('20'),
            'cost_price': Decimal('5'),
        }])
        template3, = self.Template.create([{
            'name': 'product 3',
            'type': 'goods',
            'category': category3.id,
            'list_price': Decimal('30'),
            'cost_price': Decimal('5'),
        }])
        template4, = self._create_product_template([{
            'name': 'product 4',
            'type': 'goods',
            'category': category.id,
            'list_price': Decimal('30'),
            'cost_price': Decimal('5'),
        }])
        print ">>>>>>>product1>>>>>", template1.id

        # Create Sample products
        product1, = self.Product.create([{
            'template': template1.id,
            'uri': 'product-1',
        }])
        product2, = self.Product.create([{
            'template': template2.id,
            'uri': 'product-2',
        }])
        product3, = self.Product.create([{
            'template': template3.id,
            'uri': 'product-3',
        }])
        product4, = self.Product.create([{
            'template': template4.id,
            'displayed_on_eshop': False,
            'uri': 'product-4',
        }])
        print ">>>>>>>product1>>>>>", product1.id

    def setUp(self):
        trytond.tests.test_tryton.install_module('nereid_catalog')
        self.Currency = POOL.get('currency.currency')
        self.Party = POOL.get('party.party')
        self.Product = POOL.get('product.product')
        self.Company = POOL.get('company.company')
        self.NereidUser = POOL.get('nereid.user')
        self.URLMap = POOL.get('nereid.url_map')
        self.Language = POOL.get('ir.lang')
        self.NereidWebsite = POOL.get('nereid.website')
        self.Template = POOL.get('product.template')

        self.templates = {
            'localhost/home.jinja':
            '{{request.nereid_website.get_currencies()}}',
            'localhost/login.jinja':
            '{{ login_form.errors }} {{get_flashed_messages()}}',
            'localhost/product-list.jinja':
            '{% for product in products %}'
            '|{{ product.rec_name }}|'
            '{% endfor %}',
            'localhost/category.jinja':
            '{% for product in products %}'
            '|{{ product.rec_name }}|'
            '{% endfor %}',
            'localhost/category-list.jinja':
            '{%- for category in categories %}'
            '|{{ category.name }}|'
            '{%- endfor %}',
            'localhost/search-results.jinja':
            '{% for product in products %}'
            '|{{ product.rec_name }}|'
            '{% endfor %}',
            'localhost/product.jinja': '{{ product.sale_price(product.id) }}',
            'localhost/wishlist.jinja':
            '{% for product in products %}|{{ product.uri }}|{% endfor %}',
        }

    def get_template_source(self, name):
        """
        Return templates
        """
        return self.templates.get(name)

    def test_0005_test_view(self):
        """
        Test the views
        """
        test_view('nereid_catalog')

    def test_0007_test_depends(self):
        '''
        Test Depends
        '''
        test_depends()

    def test_0010_get_price(self):
        """
        The price returned must be the list price of the product, no matter
        the quantity
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/product/product-1')
                self.assertEqual(rv.data, '10')

    def test_0020_list_view(self):
        """
        Call the render list method to get list of all products
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/products')
                self.assertEqual(rv.data, '|product 1||product 2|')

    def test_0030_category(self):
        """
        Check the category pages
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/category/category')
                self.assertEqual(rv.data, '|product 1|')

                rv = c.get('/en_US/category/category2')
                self.assertEqual(rv.data, '|product 2|')

                rv = c.get('/en_US/category/category3')
                self.assertEqual(rv.status_code, 404)

    def test_0035_category_list(self):
        """
        Test the category list pages
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/catalog')
                self.assertEqual(rv.data, '|Category||Category 2|')

    def test_0040_quick_search(self):
        """
        Check if quick search works
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/search?q=product')
                self.assertEqual(rv.data, '|product 1||product 2|')

    def test_0050_product_sitemap_index(self):
        """
        Assert that the sitemap index returns 1 result
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/sitemaps/product-index.xml')
                xml = objectify.fromstring(rv.data)
                self.assertTrue(xml.tag.endswith('sitemapindex'))
                self.assertEqual(len(xml.getchildren()), 1)

                self.assertEqual(
                    xml.sitemap.loc.pyval.split('localhost', 1)[-1],
                    '/en_US/sitemaps/product-1.xml'
                )

                rv = c.get('/en_US/sitemaps/product-1.xml')
                xml = objectify.fromstring(rv.data)
                self.assertTrue(xml.tag.endswith('urlset'))
                self.assertEqual(len(xml.getchildren()), 2)

    def test_0060_category_sitemap_index(self):
        """
        Assert that the sitemap index returns 1 result
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/sitemaps/category-index.xml')
                xml = objectify.fromstring(rv.data)
                self.assertTrue(xml.tag.endswith('sitemapindex'))
                self.assertEqual(len(xml.getchildren()), 1)

                rv = c.get(
                    xml.sitemap.loc.pyval.split('localhost/', 1)[-1]
                )
                xml = objectify.fromstring(rv.data)
                self.assertTrue(xml.tag.endswith('urlset'))
                self.assertEqual(len(xml.getchildren()), 2)

    def test_0070_get_recent_products(self):
        """
        Get the recent products list
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app(
                CACHE_TYPE='werkzeug.contrib.cache.SimpleCache'
            )

            with app.test_client() as c:
                rv = c.get('/en_US/products/+recent')
                self.assertEqual(json.loads(rv.data)['products'], [])

                rv = c.get('/en_US/product/product-1')
                rv = c.get('/en_US/products/+recent')
                self.assertEqual(len(json.loads(rv.data)['products']), 1)

                rv = c.post('/en_US/products/+recent', data={'product_id': 2})
                self.assertEqual(len(json.loads(rv.data)['products']), 2)
                rv = c.get('/en_US/products/+recent')
                self.assertEqual(len(json.loads(rv.data)['products']), 2)

    def test_0080_displayed_on_eshop(self):
        """Ensure only displayed_on_eshop products are displayed on the site
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/en_US/product/product-4')
                self.assertEqual(rv.status_code, 404)

    def test_0090_add_to_wishlist(self):
        '''Test adding products to wishlist
        '''
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            app = self.get_app()

            with app.test_client() as c:
                c.post('/en_US/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                c.post(
                    '/en_US/products/add-to-wishlist',
                    data={'product': 1}
                )
                rv = c.get('/en_US/products/view-wishlist')
                self.assertEqual(rv.data, '|product-1|')

                c.post(
                    '/en_US/products/add-to-wishlist',
                    data={'product': 2}
                )
                rv = c.get('/en_US/products/view-wishlist')
                self.assertEqual(rv.data, '|product-1||product-2|')


def suite():
    "Catalog test suite"
    test_suite = unittest.TestSuite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestCatalog)
    )
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
