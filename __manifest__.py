# -*- coding: utf-8 -*-
{
    'name': "Factura Electronica Mexico Odoo",

    'summary': """Facturacion Electronica RYE""",

    'description': """
        Personalizacion ODOO para facturacion electronica Mexico:
            - Facturacion electronica
            - Catalogos SAT
            - Produccion
    """,

    'author': "Ricardo Avila",
    'website': "http://www.rye.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','base_setup','account','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/catalogos_sat.xml',
        'views/res_company.xml',
        'views/account_invoice.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/product.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}