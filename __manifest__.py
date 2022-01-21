# -*- coding: utf-8 -*-
{
    'name': "Facturación de venta desde el sitio web",
    'description': """
        Este módulo permite facturar una venta desde el sitio web
        - Configuraciones:
            * En en menu ajustes de ventas se tiene la opcion de facturar al confirmar una venta. Si se tiene activado el enlace se muestra en el chatter de la venta
            * Se tiene un permiso (Generar enlace para facturar desde venta). Este permiso muestra en el menu de "acción" en los pedidos de venta una opción para generar el enlace de pago
        \n
        - Conexión con CFDI33:
            * Si se tiene el modulo para timbrar una factura CFDI 3.3. Entonces se mandará a timbrar despues de haber generado la factura de la venta

    """,
    'author': "Exdoo",
    'website': "http://www.exdoo.mx",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base','web','website','sale','account'],
    'data': [
        'security/ir_groups.xml',
        'security/ir.model.access.csv',
        'views/res_config.xml',
        'views/cfdi_website.xml',
        'views/cfdi_results.xml',
        'views/create_partner.xml',
        'wizards/invoice_link_wizard_views.xml',
    ],
}
