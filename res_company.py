# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

class ResCompany(models.Model):
	_inherit = 'res.company'
	usuario_facturacion = fields.Char('Usuario facturacion', size=100)
	contrasena_facturacion = fields.Char('Password facturacion',size=100)
	cuenta_facturacion = fields.Char('Cuenta facturacion',size=100)
	ip_servidor = fields.Char('IP servidor openerp',size=100)
	email_emisor = fields.Char('Email del emisor',size=100)
	folder_base = fields.Char('Folder base para archivos PDF y XML',size=100)
	c_regimenfiscal = fields.Many2one('catalogos.sat.c_regimenfiscal', 'Regimen Fiscal SAT')
	c_codigopostal = fields.Many2one('catalogos.sat.c_codigopostal', 'Codigo postal SAT')
	api_factura = fields.Char('API-Factura inteligente', size=500, default='https://www.appfacturainteligente.com/CR33TEST/ConexionRemota.svc?WSDL')
