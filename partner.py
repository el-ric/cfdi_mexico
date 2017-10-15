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

class ResPartner(models.Model):
    _inherit = 'res.partner'
    c_formapago = fields.Many2one('catalogos.sat.c_formapago', 'Forma de pago SAT')
    c_metodopago = fields.Many2one('catalogos.sat.c_metodopago', 'Metodo de pago SAT')
    c_usocfdi = fields.Many2one('catalogos.sat.c_usocfdi', 'Uso CFDI')
    c_regimenfiscal = fields.Many2one('catalogos.sat.c_regimenfiscal', 'Regimen Fiscal')
    c_codigopostal = fields.Many2one('catalogos.sat.c_codigopostal', 'Codigo postal SAT')
    def _split_vat(self, vat):
        vat_country, vat_number = 'mx', vat.replace(' ', '')
        return vat_country, vat_number
ResPartner()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

