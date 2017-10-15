# -*- coding: utf-8 -*-

import datetime

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError
import odoo.addons.decimal_precision as dp

class catalogos_sat_base(models.Model):
    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = ''.join([str(record.name),'-',record.descripcion or ''])
            res.append((record.id, name))
        return res
    _name = "catalogos.sat.base"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    #'name =  fields.Char('Nombre', size=100),
    version_catalogo_sat = fields.Char(string='Version del catalogo SAT', size=3)
    activo = fields.Boolean(string='Activo en empresa')
    descripcion =  fields.Char(string='Descripcion', size=1500)


class c_aduana(models.Model):
    _name = "catalogos.sat.c_aduana"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='Clave Aduana', size=3)

class c_claveprodserv(models.Model):

    _name = "catalogos.sat.c_claveprodserv"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_ClaveProdServ', size=10)
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')
    IncluirIVAtrasladado =  fields.Char(string='IncluirIVAtrasladado', size=15)
    IncluirIEPStrasladado =  fields.Char(string='IncluirIEPStrasladado', size=15)
    Complemento =  fields.Char(string='Complemento', size=1000)

class c_claveunidad(models.Model):
    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = ''.join([str(record.name),'-',record.nombre or ''])
            res.append((record.id, name))
        return res
    _name = "catalogos.sat.c_claveunidad"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_ClaveUnidad', size=10)
    nombre =  fields.Char(string='Nombre', size=200)
    nota =  fields.Char(string='Nota', size=300)
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')
    Simbolo =  fields.Char(string='Complemento', size=1000)

class c_codigopostal(models.Model):

    _name = "catalogos.sat.c_codigopostal"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_CodigoPostal', size=10)
    c_Estado =  fields.Char(string='Estado', size=3)
    c_Municipio =  fields.Char(string='Municipio', size=3)
    c_Localidad =  fields.Char(string='Localidad', size=2)

class c_formapago(models.Model):
    _name = "catalogos.sat.c_formapago"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_FormaPago', size=2)
    Bancarizado =  fields.Char(string='Bancarizado', size=10)
    NumeroOperacion =  fields.Char(string='Numero de operacion', size=10)
    RFCOrdenante =  fields.Char(string='RFC del Emisor de la cuenta ordenante', size=15)
    CuentaOrdenante =  fields.Char(string='Cuenta Ordenante', size=30)
    PatronCuentaOrdenante =  fields.Char(string='Patron para cuenta ordenante', size=150)
    RFCBeneficiario =  fields.Char(string='RFC del Emisor Cuenta de Beneficiario', size=15)
    CuentaBeneficiario =  fields.Char(string='Cuenta de Benenficiario', size=30)
    PatronCuentaBeneficiari0 =  fields.Char(string='Patron para cuenta Beneficiaria', size=150)
    TipoCadenaPago =  fields.Char(string='Estado', size=10)
    NombreBancoExtranjero =  fields.Char(string='Nombre del Banco emisor de la cuenta ordenante en caso de extranjero', size=150)
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')


class c_impuesto(models.Model):
    _name = "catalogos.sat.c_impuesto"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char('c_Impuesto', size=3)
    retencion =  fields.Boolean(string='Retencion')
    traslado =  fields.Boolean(string='Traslado')
    local_federal =  fields.Selection([('local','Local'),('federal','Federal')], string='Local o federal')
    entidad =  fields.Char(string='Entidad',size=20)




class c_metodopago(models.Model):
    _name = "catalogos.sat.c_metodopago"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_MetodoPago', size=3)
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')

class c_moneda(models.Model):
    _name = "catalogos.sat.c_moneda"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_Moneda', size=3)
    decimales =  fields.Integer(string='Decimales')
    porcentajeVariacion =  fields.Integer(string='Porcentaje de variacion')
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')
#Numero de pedimto aduana -- falta

class c_numpedimentoaduana(models.Model):
    _name = "catalogos.sat.c_numpedimentoaduana"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Integer(string='c_numpedimentoaduana')
    patente =  fields.Integer(string='patente')
    ejercicio =  fields.Integer(string='ejercicio')
    cantidad =  fields.Integer(string='cantidad')
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')

class c_patenteaduanal(models.Model):
    _name = "catalogos.sat.c_patenteaduanal"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Integer(string='c_PatenteAduanal')
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')

class c_regimenfiscal(models.Model):
    _name = "catalogos.sat.c_regimenfiscal"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Integer(string='c_RegimenFiscal')
    personaFisica =  fields.Boolean(string='Aplica persona fisica')
    personaMoral =  fields.Boolean(string='Aplica persona moral')
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')

class c_tipodecomprobante(models.Model):
    _name = "catalogos.sat.c_tipodecomprobante"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_TipoDeComprobante', size=1)
    valorMaximo =  fields.Float(string='Valor maximo')
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')

class c_tipofactor(models.Model):
    _name = "catalogos.sat.c_tipofactor"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_TipoFactor', size=10)

class c_tiporelacion(models.Model):
    _name = "catalogos.sat.c_tiporelacion"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_TipoRelacion', size=2)
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')


class c_usocfdi(models.Model):
    _name = "catalogos.sat.c_usocfdi"
    _description = "Catalogos oficiales del SAT para emision de CFDI"
    _inherit = "catalogos.sat.base"
    name =  fields.Char(string='c_UsoCFDI', size=5)
    personaFisica =  fields.Boolean(string='Aplica persona fisica')
    personaMoral =  fields.Boolean(string='Aplica persona moral')
    FechaInicioVigencia =  fields.Date(string='Fecha inicio de vigencia')
    FechaFinVigencia =  fields.Date(string='Fecha fin de vigencia')