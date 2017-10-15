# -*- coding: utf-8 -*-

import datetime

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError
import odoo.addons.decimal_precision as dp

class sale_order(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'
    _description= 'Sales Order'
    c_formapago = fields.Many2one('catalogos.sat.c_formapago', 'Forma de pago SAT')
    c_metodopago = fields.Many2one('catalogos.sat.c_metodopago', 'Metodo de pago SAT')
    c_usocfdi = fields.Many2one('catalogos.sat.c_usocfdi', 'Uso CFDI')
    
    @api.onchange('partner_id') 
    def _onchange_partner_id(self):
        result = super(sale_order, self).onchange_partner_id()
        if self.partner_id:
            self.c_formapago = self.partner_id.c_formapago and self.partner_id.c_formapago.id or False
            self.c_metodopago = self.partner_id.c_metodopago and self.partner_id.c_metodopago.id or False
            self.c_usocfdi = self.partner_id.c_usocfdi and self.partner_id.c_usocfdi.id or False
        return result
    
    def _prepare_invoice(self):

        invoice_vals = super(sale_order, self)._prepare_invoice()
        invoice_vals['c_formapago'] = self.c_formapago.id
        invoice_vals['c_metodopago'] = self.c_metodopago.id
        invoice_vals['c_usocfdi'] = self.c_usocfdi.id
        return invoice_vals