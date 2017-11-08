# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 12:41:26 2017

@author: Ricardo
"""

from openerp import api, fields, models, _
from openerp.tools import float_is_zero, float_compare
from openerp.tools.misc import formatLang
from openerp.exceptions import Warning
#import urllib.parse, urllib.request
import urllib2
import ssl
import xml.etree.ElementTree as ET
import time
from datetime import date
import os
import base64
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    url = "https://www.appfacturainteligente.com/CR33TEST/ConexionRemota.svc?WSDL"
    @api.multi
    def guarda_adjunto(self,nombre,datos,tipo):
        self.env['ir.attachment'].create({
        'name': nombre,
        'type': 'binary',
        'datas': base64.encodestring(datos),
        'datas_fname':nombre,
        'res_model': 'account.invoice',
        'res_id': self.id,
        'mimetype': tipo
        })
        
    @api.multi
    def guardar_archivo(self,datos,nombre_archivo,modo):
        file = open(nombre_archivo,modo)
        file.write(datos)
        file.close()
    @api.multi
    def obtener_carpeta_dia(self):
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        add_dir = os.path.join(dir_path, 'CFDI_emitidos',str(date.today().year),str(date.today().month),str(date.today().day))
        xml = os.path.join(add_dir,"xml")
        pdf = os.path.join(add_dir,"pdf")
        solicitudes = os.path.join(add_dir,"solicitudes")
        if(os.path.exists(add_dir)==False):
            os.makedirs(xml, 0700)
            os.makedirs(pdf, 0700)
            os.makedirs(solicitudes, 0700)
        return {'xml':xml,'pdf':pdf,'solicitudes':solicitudes}
    @api.multi
    def envia_email(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        if self.state != 'open':
            raise Warning(_('Factura no validada, no es posible emitir factura electronica.'))
        if not self.partner_id.email:
            raise Warning(_('Cliente no cuenta con email registrado'))
        soap_request = "<?xml version=\"1.0\"?>"
        soap_request = ''.join([soap_request,"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:tem=\"http://tempuri.org/\" xmlns:tes=\"http://schemas.datacontract.org/2004/07/TES.V33.CFDI.Negocios\">"])
        soap_request = ''.join([soap_request,"<soapenv:Header/>"])
        soap_request = ''.join([soap_request,"<soapenv:Body>"])
        soap_request = ''.join([soap_request,"    <tem:EnviarCFDI>"])
        soap_request = ''.join([soap_request,"    <tem:credenciales>"])
        soap_request = ''.join([soap_request,"    <tes:Cuenta>", company.cuenta_facturacion ,"</tes:Cuenta>"])
        soap_request = ''.join([soap_request,"    <tes:Password>", company.contrasena_facturacion ,"</tes:Password>"])
        soap_request = ''.join([soap_request,"    <tes:Usuario>", company.usuario_facturacion ,"</tes:Usuario>"])
        soap_request = ''.join([soap_request,"    </tem:credenciales>"])
        soap_request  = ''.join([soap_request, "    <tem:uuid>", self.uuid_factura ,"</tem:uuid>"])
        soap_request  = ''.join([soap_request, "    <tem:email>", self.partner_id.email ,",", company.email_emisor,"</tem:email>"])
        soap_request  = ''.join([soap_request, "    <tem:titulo>", company.name, " Factura: ", self.number  ,"</tem:titulo>"])
        soap_request  = ''.join([soap_request, "    </tem:EnviarCFDI>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Body>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Envelope>"])
        
        url = self.url
        
        data = soap_request.encode('UTF-8', errors='replace') # data should be bytes
        header = {"Host":" www.fel.mx",
                  "Content-Type":"text/xml; charset=UTF-8",
                  "Content-Length":len(data),
                  "SOAPAction":"\"http://tempuri.org/IConexionRemota/EnviarCFDI\""}
        
        #FIX SSL CERTIFICATES
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib2.Request(url,data,header)
        
        try: r = urllib2.urlopen(req,context=ctx)
        except urllib.error.URLError as e:
            raise Warning(_(''.join(['Error al obtener PDF: ', e.reason])))
            print("ERROR")
            print(e.reason)
          
        xml_respuesta = r.read()
        root = ET.fromstring(xml_respuesta)
        self.mensaje_cfdi = ''.join([self.mensaje_cfdi,' - Email enviado: ', self.partner_id.email, '|', company.email_emisor])

    @api.multi
    def obtiene_creditos(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        soap_request = "<?xml version=\"1.0\"?>"
        soap_request = ''.join([soap_request,"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:tem=\"http://tempuri.org/\" xmlns:tes=\"http://schemas.datacontract.org/2004/07/TES.V33.CFDI.Negocios\">"])
        soap_request = ''.join([soap_request,"<soapenv:Header/>"])
        soap_request = ''.join([soap_request,"<soapenv:Body>"])
        soap_request = ''.join([soap_request,"    <tem:ObtenerNumerosCreditos>"])
        soap_request = ''.join([soap_request,"    <tem:credenciales>"])
        soap_request = ''.join([soap_request,"    <tes:Cuenta>", company.cuenta_facturacion ,"</tes:Cuenta>"])
        soap_request = ''.join([soap_request,"    <tes:Password>", company.contrasena_facturacion ,"</tes:Password>"])
        soap_request = ''.join([soap_request,"    <tes:Usuario>", company.usuario_facturacion ,"</tes:Usuario>"])
        soap_request = ''.join([soap_request,"    </tem:credenciales>"])
        soap_request  = ''.join([soap_request, "    </tem:ObtenerNumerosCreditos>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Body>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Envelope>"])
        
        url = self.url
        
        data = soap_request.encode('UTF-8', errors='replace') # data should be bytes
        header = {"Host":" www.fel.mx",
                  "Content-Type":"text/xml; charset=UTF-8",
                  "Content-Length":len(data),
                  "SOAPAction":"\"http://tempuri.org/IConexionRemota/ObtenerNumerosCreditos\""}
        
        #FIX SSL CERTIFICATES
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib2.Request(url,data,header)
        
        try: r = urllib2.urlopen(req,context=ctx)
        except urllib.error.URLError as e:
            raise Warning(_(''.join(['Error al obtener PDF: ', e.reason])))
            print("ERROR")
            print(e.reason)
          
        xml_respuesta = r.read()
        root = ET.fromstring(xml_respuesta)
        raise Warning(_(''.join(['Creditos disponibles: ', root[0][0][0][0].text, ' Creditos utilizados:',root[0][0][0][1].text])))


    @api.multi
    def cancelar_cfdi(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        if self.state != 'open':
            raise Warning(_('Factura no validada, no es posible emitir factura electronica.'))
        soap_request = "<?xml version=\"1.0\"  encoding=\"utf-8\"?>"
        soap_request = ''.join([soap_request,"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:tem=\"http://tempuri.org/\" xmlns:tes=\"http://schemas.datacontract.org/2004/07/TES.V33.CFDI.Negocios\">"])
        soap_request = ''.join([soap_request,"<soapenv:Header/>"])
        soap_request = ''.join([soap_request,"<soapenv:Body>"])
        soap_request = ''.join([soap_request,"<tem:CancelarCFDIs>"])
        soap_request = ''.join([soap_request,"<tem:credenciales>"])
        soap_request = ''.join([soap_request,"<tes:Cuenta>", company.cuenta_facturacion ,"</tes:Cuenta>"])
        soap_request = ''.join([soap_request,"<tes:Password>", company.contrasena_facturacion ,"</tes:Password>"])
        soap_request = ''.join([soap_request,"<tes:Usuario>", company.usuario_facturacion ,"</tes:Usuario>"])
        soap_request = ''.join([soap_request,"</tem:credenciales>"])
        soap_request  = ''.join([soap_request, "<tem:uuids><string>", self.uuid_factura ,"</string></tem:uuids>"])
        soap_request  = ''.join([soap_request, "</tem:CancelarCFDIs>"])
        soap_request  = ''.join([soap_request, "</soapenv:Body>"])
        soap_request  = ''.join([soap_request, "</soapenv:Envelope>"])
        
        url = self.url
        
        data = soap_request.encode('UTF-8', errors='replace') # data should be bytes
        header = {"Host":" www.fel.mx",
                  "Content-Type":"text/xml; charset=UTF-8",
                  "Content-Length":len(data),
                  "SOAPAction":"\"http://tempuri.org/IConexionRemota/ObtenerPDF\""}
        
        #FIX SSL CERTIFICATES
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib2.Request(url,data,header)
        carpetas = self.obtener_carpeta_dia()
        nombre_archivo_factura = ''.join([str(self.id),"-",self.partner_id.vat])
        self.guardar_archivo(data,''.join([carpetas['xml'],'/XMLCancelacion-',nombre_archivo_factura,'.xml']),"wb")

        try: r = urllib2.urlopen(req,context=ctx)
        except urllib2.error.URLError as e:
            raise Warning(_(''.join(['Error al obtener PDF: ', e.reason])))
            print("ERROR")
            print(e.reason)
        self.mensaje_cfdi = 'Factura cancelada en PAC'
        self.estado_cfdi = 'cancelado'
        self.obtiene_pdf()

    @api.multi
    def obtiene_pdf(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        if self.state != 'open':
            raise Warning(_('Factura no validada, no es posible emitir factura electronica.'))
        soap_request = "<?xml version=\"1.0\"?>"
        soap_request = ''.join([soap_request,"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:tem=\"http://tempuri.org/\" xmlns:tes=\"http://schemas.datacontract.org/2004/07/TES.V33.CFDI.Negocios\">"])
        soap_request = ''.join([soap_request,"<soapenv:Header/>"])
        soap_request = ''.join([soap_request,"<soapenv:Body>"])
        soap_request = ''.join([soap_request,"    <tem:ObtenerPDF>"])
        soap_request = ''.join([soap_request,"    <tem:credenciales>"])
        soap_request = ''.join([soap_request,"    <tes:Cuenta>", company.cuenta_facturacion ,"</tes:Cuenta>"])
        soap_request = ''.join([soap_request,"    <tes:Password>", company.contrasena_facturacion ,"</tes:Password>"])
        soap_request = ''.join([soap_request,"    <tes:Usuario>", company.usuario_facturacion ,"</tes:Usuario>"])
        soap_request = ''.join([soap_request,"    </tem:credenciales>"])
        soap_request  = ''.join([soap_request, "    <tem:uuid>", self.uuid_factura ,"</tem:uuid>"])
        soap_request  = ''.join([soap_request, "    </tem:ObtenerPDF>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Body>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Envelope>"])
        
        url = self.url
        
        data = soap_request.encode('UTF-8', errors='replace') # data should be bytes
        header = {"Host":" www.fel.mx",
                  "Content-Type":"text/xml; charset=UTF-8",
                  "Content-Length":len(data),
                  "SOAPAction":"\"http://tempuri.org/IConexionRemota/ObtenerPDF\""}
        
        #FIX SSL CERTIFICATES
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib2.Request(url,data,header)
        
        try: r = urllib2.urlopen(req,context=ctx)
        except urllib.error.URLError as e:
            raise Warning(_(''.join(['Error al obtener PDF: ', e.reason])))
            print("ERROR")
            print(e.reason)
          
        xml_respuesta = r.read()
        carpetas = self.obtener_carpeta_dia()
        #nombre_archivo_factura = $numero_factura ."-" .$rfc
        nombre_archivo_factura = ''.join([str(self.id),"-",self.partner_id.vat])
        self.guardar_archivo(xml_respuesta,''.join([carpetas['xml'],'/XMLpdf-',nombre_archivo_factura,'.xml']),"wb")
        root = ET.fromstring(xml_respuesta)
        if(root[0][0][0][4].text == 'false'):
            raise Warning(_(''.join(['Error al obtener PDF: ', root[0][0][0][3].text])))
        else:
            pdf_contenido = base64.b64decode(root[0][0][0][5].text)
            self.guardar_archivo(pdf_contenido,''.join([carpetas['pdf'],'/PDF-',nombre_archivo_factura,'.pdf']),"wb")
            #self.guardar_archivo(data,''.join([carpetas['pdf'],'/RequestPDF-',nombre_archivo_factura,'.xml']),"w")
            self.guarda_adjunto(nombre_archivo_factura + '.pdf',pdf_contenido,'application/x-pdf' )

    @api.multi
    def hola_cfdi(self):
        self.obtiene_pdf()
    @api.multi
    def emite_cfdi(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        if self.state != 'open':
            raise Warning(_('Factura no validada, no es posible emitir factura electronica.'))
        soap_request = "<?xml version=\"1.0\"?>"
        soap_request = ''.join([soap_request,"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:tem=\"http://tempuri.org/\" xmlns:tes=\"http://schemas.datacontract.org/2004/07/TES.V33.CFDI.Negocios\">"])
        soap_request = ''.join([soap_request,"<soapenv:Header/>"])
        soap_request = ''.join([soap_request,"<soapenv:Body>"])
        soap_request = ''.join([soap_request,"    <tem:GenerarCFDI>"])
        
        
        soap_request = ''.join([soap_request,"    <tem:credenciales>"])
        soap_request = ''.join([soap_request,"    <tes:Cuenta>", company.cuenta_facturacion ,"</tes:Cuenta>"])
        soap_request = ''.join([soap_request,"    <tes:Password>", company.contrasena_facturacion ,"</tes:Password>"])
        soap_request = ''.join([soap_request,"    <tes:Usuario>", company.usuario_facturacion ,"</tes:Usuario>"])
        soap_request = ''.join([soap_request,"    </tem:credenciales>"])
        
        soap_request = ''.join([soap_request,"    <tem:cfdi>"])
        
        #Forma de pago del documento CFDi (REQUERIDO).
        soap_request  = ''.join([soap_request, "    <tes:ClaveCFDI>FAC</tes:ClaveCFDI>"])
          
        #Subtotal del documento CFDi (REQUERIDO).
        soap_request  = ''.join([soap_request, "    <tes:Conceptos>"])
         
        for line in self.invoice_line_ids:
            soap_request  = ''.join([soap_request, "  <tes:ConceptoR>"])
            soap_request  = ''.join([soap_request, "    <tes:Cantidad>",str(line.quantity),"</tes:Cantidad>"])
            soap_request  = ''.join([soap_request, "    <tes:ClaveProdServ>",str(line.product_id.product_tmpl_id.c_claveprodserv.name),"</tes:ClaveProdServ>"])
            soap_request  = ''.join([soap_request, "    <tes:ClaveUnidad>",str(line.uom_id.c_claveunidad.name),"</tes:ClaveUnidad>"])
            desc = line.name
            soap_request  = u''.join([soap_request, "    <tes:Descripcion>",str.strip(desc),"</tes:Descripcion>"])
            soap_request  = ''.join([soap_request, "    <tes:Importe>",str(line.price_subtotal),"</tes:Importe>"])
            soap_request  = ''.join([soap_request, "    <tes:Impuestos>"])
            soap_request  = ''.join([soap_request, "    <tes:Traslados>"])
            for impuestos in line.invoice_line_tax_ids:
                soap_request  = ''.join([soap_request, "    <tes:TrasladoConceptoR>"])
                soap_request  = ''.join([soap_request, "    <tes:Base>",str(line.price_subtotal),"</tes:Base>"])
                soap_request  = ''.join([soap_request, "    <tes:Importe>",str(line.price_subtotal * (impuestos.amount / 100 )),"</tes:Importe>"])
                soap_request  = ''.join([soap_request, "    <tes:Impuesto>002</tes:Impuesto>"])
                soap_request  = ''.join([soap_request, "    <tes:TasaOCuota>",str( '{0:.6f}'.format(impuestos.amount / 100)),"</tes:TasaOCuota>"])
                soap_request  = ''.join([soap_request, "    <tes:TipoFactor>Tasa</tes:TipoFactor>"])
                soap_request  = ''.join([soap_request, "    </tes:TrasladoConceptoR>"])
            soap_request  = ''.join([soap_request, "    </tes:Traslados>"])
            soap_request  = ''.join([soap_request, "    </tes:Impuestos>"])
            soap_request  = ''.join([soap_request, "    <tes:NoIdentificacion>",str(line.product_id.default_code),"</tes:NoIdentificacion>"])
            soap_request  = ''.join([soap_request, "  <tes:Unidad>",str(line.uom_id.name),"</tes:Unidad>"])
            soap_request  = ''.join([soap_request, "    <tes:ValorUnitario>",str(line.price_unit),"</tes:ValorUnitario>"])
            soap_request  = ''.join([soap_request, "    </tes:ConceptoR>"])
        
        soap_request  = ''.join([soap_request, "    </tes:Conceptos>"])
          
          
        #  /*************************************************************************************
        ## Sección de variables para la descripción de los conceptos
        #   *************************************************************************************/ 
           
        #   /************************************************************************************
        #                 CONCEPTO 1
        #   ************************************************************************************/ 
        soap_request  = ''.join([soap_request, "    <tes:CondicionesDePago>",str(self.payment_term_id.name),"</tes:CondicionesDePago>"])
          
          #Cantidad, Unidad, Descripcion, ValorUnitario e Importe del Concepto. (REQUERIDOS)
        soap_request  = ''.join([soap_request, "	<tes:Emisor>"])
          
          #Seccion para detallar el impuesto por partida (Opcional).
          #Se indica el tipo de calculo que se realizara por cada Concepto (PARTIDA, IEPS_GASOLINA, IEPS_TABACO)
        soap_request  = ''.join([soap_request, "    <tes:Nombre>",str(company.name),"</tes:Nombre>"])
        soap_request  = ''.join([soap_request, "    <tes:RegimenFiscal>",str(company.c_regimenfiscal.name),"</tes:RegimenFiscal>"])
          
          #Seccion para indicar el descuento por partida.
        soap_request  = ''.join([soap_request, "    </tes:Emisor>"])
          
          #Seccion para indicar las retenciones por partida.
        soap_request  = ''.join([soap_request, "    <tes:Fecha>",str(self.date_invoice),"</tes:Fecha>"])
        soap_request  = ''.join([soap_request, "    <tes:Folio>",str(self.number),"</tes:Folio>"])
        soap_request  = ''.join([soap_request, "    <tes:FormaPago>",str(self.c_formapago.name),"</tes:FormaPago>"])
        soap_request  = ''.join([soap_request, "    <tes:LugarExpedicion>",str(company.c_codigopostal.name),"</tes:LugarExpedicion>"])
        soap_request  = ''.join([soap_request, "    <tes:MetodoPago>",str(self.c_metodopago.name),"</tes:MetodoPago>"])
          
          #Seccion para indicar las retenciones locales por partida.
        soap_request  = ''.join([soap_request, "    <tes:Moneda>",str(self.currency_id.name),"</tes:Moneda>"])
        soap_request  = ''.join([soap_request, "    <tes:Receptor>"])   
        soap_request  = ''.join([soap_request, "    <tes:Nombre>",str(self.partner_id.name).encode('UTF-8', errors='replace'),"</tes:Nombre>"])
        soap_request  = ''.join([soap_request, "    <tes:Rfc>",str(self.partner_id.vat),"</tes:Rfc>"])
        soap_request  = ''.join([soap_request, "    <tes:UsoCFDI>",str(self.c_usocfdi.name),"</tes:UsoCFDI>"])
          
          #Seccion para indicar los impuestos de traslado por partida partida.
        soap_request  = ''.join([soap_request, "    </tes:Receptor>"])
        soap_request  = ''.join([soap_request, "    <tes:Referencia>",str(self.reference),"</tes:Referencia>"])
        soap_request  = ''.join([soap_request, "    <tes:Serie>A</tes:Serie>"])
        soap_request  = ''.join([soap_request, "    <tes:SubTotal>",str(self.amount_untaxed),"</tes:SubTotal>"])
        soap_request  = ''.join([soap_request, "    <tes:TipoCambio>1</tes:TipoCambio>"])
          
          #Seccion para indicar los impuestos de traslado locales por partida partida.
        soap_request  = ''.join([soap_request, "    <tes:Total>",str(self.amount_total),"</tes:Total>"])
        soap_request  = ''.join([soap_request, "    </tem:cfdi>"])
        soap_request  = ''.join([soap_request, "    </tem:GenerarCFDI>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Body>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Envelope>"])
        
        url = self.url
        #url = 'https://www.appfacturainteligente.com/CR33TEST/ConexionRemota.svc?WSDL'
        _logger.info(url)
        
        data = soap_request.encode('UTF-8', errors='replace') # data should be bytes
        header = {"Host":" www.fel.mx",
                  "Content-Type":"text/xml; charset=UTF-8",
                  "Content-Length":len(data),
                  "SOAPAction":"\"http://tempuri.org/IConexionRemota/GenerarCFDI\""}
        
        #FIX SSL CERTIFICATES
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib2.Request(url,data,header)
        
        try: r = urllib2.urlopen(req,context=ctx)
        except urllib2.URLError as e:
            raise Warning(_(u''.join([u'Error al emitir CFDI: ', e.reason])))
            _logger.info("ERROR")
            _logger.info(e.reason)

          
        xml_respuesta = r.read()
        carpetas = self.obtener_carpeta_dia()
        #nombre_archivo_factura = $numero_factura ."-" .$rfc
        nombre_archivo_factura = ''.join([str(self.id),"-",self.partner_id.vat])
        self.guardar_archivo(xml_respuesta,''.join([carpetas['solicitudes'],'/RespuestaWS-',nombre_archivo_factura,'.xml']),"wb")
        self.guardar_archivo(data,''.join([carpetas['solicitudes'],'/SolicitudWS-',nombre_archivo_factura,'.xml']),"wb")
        
        
        
        root = ET.fromstring(xml_respuesta)
        CBB = root[0][0][0][0].text
        OperacionExitosa = root[0][0][0][4].text
        
        if(OperacionExitosa=="true"):
            XML = root[0][0][0][6].text
            self.guardar_archivo(XML,''.join([carpetas['xml'],'/',nombre_archivo_factura,'.xml']),"w")
            CodigoConfirmacion = root[0][0][0][1].text
            xml_cfdi = ET.fromstring(XML)
            folio = xml_cfdi.attrib['Folio']
            sello = xml_cfdi.attrib['Sello']
            uuid = xml_cfdi[4][0].attrib['UUID']
            print('Operacion Exitosa')
            self.estado_cfdi = 'valido'
            self.mensaje_cfdi = 'Factura emitida'
            self.sello = sello
            self.uuid_factura = uuid
            self.fecha_ultimo_cfdi = fields.Datetime.now()
            self.envia_email()
            self.obtiene_pdf()

        else:
            ErrorDetallado = root[0][0][0][2].text
            ErrorGeneral = root[0][0][0][3].text
            _logger.info('Error en emision de CFDI')
            self.error_cfdi = ErrorGeneral
            self.error_cfdi_detalle = ErrorDetallado
            self.estado_cfdi = 'error'