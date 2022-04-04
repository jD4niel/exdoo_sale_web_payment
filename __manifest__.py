# -*- coding: utf-8 -*-
{
    'name': "Pagos de venta desde el sitio web",
    'description': """
        Este módulo permite pagar una venta desde el sitio web
        * pip install mercadopago
 
    """,
    'author': "Exdoo",
    'website': "http://www.exdoo.mx",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base','web','website','sale','account'],
    'data': [
        'views/assets.xml',
        'security/ir_groups.xml',
        'security/ir.model.access.csv',
        'views/res_config.xml',
        'views/sale_website.xml',
        'wizards/payment_link_wizard_views.xml',
    ],
}
