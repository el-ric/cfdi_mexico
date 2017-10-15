# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError
import odoo.addons.decimal_precision as dp

class product_product(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    _description= 'Productos'
    
    c_claveprodserv = fields.Many2one('catalogos.sat.c_claveprodserv', 'Productos y servicios SAT')



class product_uom(models.Model):
    _name = 'product.uom'
    _inherit = 'product.uom'
    _description = 'Product Unit of Measure'
    c_claveunidad = fields.Many2one('catalogos.sat.c_claveunidad', 'Catalogo unidades de medida SAT')
    