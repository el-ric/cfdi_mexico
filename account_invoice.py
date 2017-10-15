# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.tools import float_is_zero, float_compare
from openerp.tools.misc import formatLang

from openerp.exceptions import UserError, RedirectWarning, ValidationError

import openerp.addons.decimal_precision as dp
import amount_to_text_es_MX
import urllib,urllib2
import time
import threading

class MyHandler(urllib2.HTTPHandler):
    def http_response(self, req, response):
        return response
class AccountInvoice(models.Model):
	_inherit = 'account.invoice'
	estado_cfdi = fields.Selection([
			('no_enviado','No enviado'),
			('procesando','Procesando'),
			('valido','Factura emitida'),
			('error','ERROR AL FACTURAR'),
			('cancelado','Cancelado'),
			('en_espera','En espera'),]
		,'CFDI - Estado facturacion', select=True, required=True, default='no_enviado')
	mensaje_cfdi = fields.Char('Mensaje PAC',readonly=True, size=500, default='')
	uuid_factura = fields.Char('Folio oficial UUID',readonly=True, size=500, default='')
	fecha_ultimo_cfdi = fields.Datetime('Fecha ultimo movimiento con PAC')
	amount_to_text =  fields.Char(compute='_get_amount_to_text', method=True,
		type='char', size=256, string='Amount to Text', store=True,
		help='Amount of the invoice in letter')
	c_formapago = fields.Many2one('catalogos.sat.c_formapago', 'Forma de pago SAT',ondelete = 'Cascade')
	c_metodopago = fields.Many2one('catalogos.sat.c_metodopago', 'Metodo de pago SAT',ondelete = 'Cascade')
	c_usocfdi = fields.Many2one('catalogos.sat.c_usocfdi', 'Uso CFDI',ondelete = 'Cascade')
	error_cfdi = fields.Char('Error CFDI',readonly=True, size=5000, default='')
	error_cfdi_detalle = fields.Char('Error CFDI detalles',readonly=True, size=5000, default='')
	sello = fields.Text('Sello CFDI',readonly=True, default='')

	@api.model
	def _get_amount_to_text(self):
		if not context:
			context = {}
		res = {}
		for invoice in self.browse(cr, uid, ids, context=context):
			amount_to_text = amount_to_text_es_MX.get_amount_to_text(
				self, invoice.amount_total, 'es_cheque', 'code' in invoice.\
				currency_id._columns and invoice.currency_id.code or invoice.\
				currency_id.name)
			res[invoice.id] = amount_to_text
		return res

		
		
	@api.model
	def action_cancel(self):
		self.cancelar_cfdi()
		super(AccountInvoice, self).action_cancel()
		return True