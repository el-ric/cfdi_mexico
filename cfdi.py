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
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    array_offset = 0
    
    
    def normalize(self,name):
        if name[0] == "{":
            uri, tag = name[1:].split("}")
            return tag
        else:
            return name
    
    def obtiene_url(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        url_prueba = "https://www.appfacturainteligente.com/CR33TEST/ConexionRemota.svc?WSDL"

        if(company.api_factura == url_prueba):
            self.array_offset = 2
            _logger.info("Cambio de offset")
            _logger.info(self.array_offset)
        return company.api_factura
        
    
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
            self.mensaje_cfdi = ''.join([self.mensaje_cfdi,' - Cliente no cuenta con email registrado'])
            pass
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
        soap_request  = ''.join([soap_request, "    <tem:email>", self.partner_id.email or 'void@mail.com' ,",", company.email_emisor,"</tem:email>"])
        soap_request  = ''.join([soap_request, "    <tem:titulo>", company.name, " Factura: ", self.number  ,"</tem:titulo>"])
        soap_request  = ''.join([soap_request, "    </tem:EnviarCFDI>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Body>"])
        soap_request  = ''.join([soap_request, "    </soapenv:Envelope>"])
        
        url = self.obtiene_url()
        
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
        except urllib2.URLError as e:
            raise Warning(_(''.join(['Error al obtener PDF: ', e.reason])))
            print("ERROR")
            print(e.reason)
          
        xml_respuesta = r.read()
        root = ET.fromstring(xml_respuesta)
        self.mensaje_cfdi = ''.join([self.mensaje_cfdi,' - Email enviado: ', self.partner_id.email or 'void@mail.com', '|', company.email_emisor])

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

        url = self.obtiene_url()
        
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
        except urllib2.URLError as e:
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
        soap_request  = ''.join([soap_request, "<tem:uuids><tes:uuid>", self.uuid_factura ,"</tes:uuid></tem:uuids>"])
        soap_request  = ''.join([soap_request, "</tem:CancelarCFDIs>"])
        soap_request  = ''.join([soap_request, "</soapenv:Body>"])
        soap_request  = ''.join([soap_request, "</soapenv:Envelope>"])
        _logger.info('Cancela CFDI')
        url = self.obtiene_url()
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
        _logger.info(data)
        try: r = urllib2.urlopen(req,context=ctx)
        except urllib2.URLError as e:
            raise Warning(_(''.join(['Error al cancelar CFDI: ', e.reason])))
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
        soap_request = ''.join([soap_request,"<tem:ObtenerPDF>"])
        soap_request = ''.join([soap_request,"<tem:credenciales>"])
        soap_request = ''.join([soap_request,"<tes:Cuenta>", company.cuenta_facturacion ,"</tes:Cuenta>"])
        soap_request = ''.join([soap_request,"<tes:Password>", company.contrasena_facturacion ,"</tes:Password>"])
        soap_request = ''.join([soap_request,"<tes:Usuario>", company.usuario_facturacion ,"</tes:Usuario>"])
        soap_request = ''.join([soap_request,"</tem:credenciales>"])
        soap_request  = ''.join([soap_request, "<tem:uuid>", self.uuid_factura ,"</tem:uuid>"])
        soap_request  = ''.join([soap_request, "</tem:ObtenerPDF>"])
        soap_request  = ''.join([soap_request, "</soapenv:Body>"])
        soap_request  = ''.join([soap_request, "</soapenv:Envelope>"])
        
        url = self.obtiene_url()
        
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
        except urllib2.URLError as e:
            raise Warning(_(''.join(['Error al obtener PDF: ', e.reason])))
            print("ERROR")
            print(e.reason)
          
        xml_respuesta = r.read()
        carpetas = self.obtener_carpeta_dia()
        #nombre_archivo_factura = $numero_factura ."-" .$rfc
        nombre_archivo_factura = ''.join([str(self.id),"-",self.partner_id.vat])
        self.guardar_archivo(xml_respuesta,''.join([carpetas['xml'],'/XMLpdf-',nombre_archivo_factura,'.xml']),"wb")
        root = ET.fromstring(xml_respuesta)
        for elem in root.getiterator():
            if(self.normalize(elem.tag) == 'OperacionExitosa'):
                operacion_exitosa = elem.text
            if(self.normalize(elem.tag) == 'ErrorDetallado'):
                ErrorDetallado = elem.text
            if(self.normalize(elem.tag) == 'ErrorGeneral'):
                ErrorGeneral = elem.text
            if(self.normalize(elem.tag) == 'PDF'):
                PDF = elem.text
            if(self.normalize(elem.tag) == 'XML'):
                XML = elem.text
        if(operacion_exitosa == 'false'):
            raise Warning(_(''.join(['Error al obtener PDF: ', ErrorDetallado])))
        else:
            pdf_contenido = base64.b64decode(PDF)
            self.guardar_archivo(pdf_contenido,''.join([carpetas['pdf'],'/PDF-',nombre_archivo_factura,'.pdf']),"wb")
            #self.guardar_archivo(data,''.join([carpetas['pdf'],'/RequestPDF-',nombre_archivo_factura,'.xml']),"w")
            self.guarda_adjunto(nombre_archivo_factura + '.pdf',pdf_contenido,'application/x-pdf' )

    @api.multi
    def hola_cfdi(self):
        self.obtiene_pdf()
    @api.multi
    def emite_cfdi(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        descuento_total = 0
        if self.state != 'open':
            raise Warning(_('Factura no validada, no es posible emitir factura electronica.'))
        soap_request = "<?xml version=\"1.0\"?>"
        soap_request = u''.join([soap_request,"<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:tem=\"http://tempuri.org/\" xmlns:tes=\"http://schemas.datacontract.org/2004/07/TES.V33.CFDI.Negocios\">"]).encode('UTF-8', errors='replace')
        soap_request = u''.join([soap_request,"<soapenv:Header/>"]).encode('UTF-8', errors='replace')
        soap_request = u''.join([soap_request,"<soapenv:Body>"]).encode('UTF-8', errors='replace')
        soap_request = u''.join([soap_request,"<tem:GenerarCFDI>"]).encode('UTF-8', errors='replace')
        
        
        soap_request = u''.join([soap_request,"<tem:credenciales>"]).encode('UTF-8', errors='replace')
        soap_request = u''.join([soap_request,"<tes:Cuenta>", company.cuenta_facturacion ,"</tes:Cuenta>"]).encode('UTF-8', errors='replace')
        soap_request = u''.join([soap_request,"<tes:Password>", company.contrasena_facturacion ,"</tes:Password>"]).encode('UTF-8', errors='replace')
        soap_request = u''.join([soap_request,"<tes:Usuario>", company.usuario_facturacion ,"</tes:Usuario>"]).encode('UTF-8', errors='replace')
        soap_request = u''.join([soap_request,"</tem:credenciales>"]).encode('UTF-8', errors='replace')
        
        soap_request = ''.join([soap_request,"<tem:cfdi>"])

        soap_request  = ''.join([soap_request, "<tes:ClaveCFDI>FAC</tes:ClaveCFDI>"])

        soap_request  = u''.join([soap_request, "<tes:Conceptos>"])
         
        for line in self.invoice_line_ids:
            soap_request  = u''.join([soap_request, "<tes:ConceptoR>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:Cantidad>",str(line.quantity),"</tes:Cantidad>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:ClaveProdServ>",str(line.product_id.product_tmpl_id.c_claveprodserv.name),"</tes:ClaveProdServ>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:ClaveUnidad>",str(line.uom_id.c_claveunidad.name),"</tes:ClaveUnidad>"]).encode('UTF-8', errors='replace')
            descuento = (line.price_unit * line.quantity) * (line.discount / 100)
            descuento_unidad = round((line.price_unit) * (1 - (line.discount / 100)),4)
            descuento_total += descuento
            desc = line.name
            if (line.discount > 0):
                desc = u''.join([desc, ': Descuento aplicado: ', str(line.discount), ' - $', str(descuento)]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:Descripcion>",str.strip(str(desc)),"</tes:Descripcion>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:Importe>",str((line.price_subtotal)),"</tes:Importe>"]).encode('UTF-8', errors='replace')
            
            #soap_request  = ''.join([soap_request, "<tes:Descuento>",str(descuento),"</tes:Descuento>"])
            soap_request  = u''.join([soap_request, "<tes:Impuestos>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:Traslados>"]).encode('UTF-8', errors='replace')
            for impuestos in line.invoice_line_tax_ids:
                soap_request  = u''.join([soap_request, "<tes:TrasladoConceptoR>"]).encode('UTF-8', errors='replace')
                soap_request  = u''.join([soap_request, "<tes:Base>",str(line.price_subtotal),"</tes:Base>"]).encode('UTF-8', errors='replace')
                soap_request  = u''.join([soap_request, "<tes:Importe>",str(round(line.price_subtotal * (impuestos.amount / 100 ),2)),"</tes:Importe>"]).encode('UTF-8', errors='replace')
                soap_request  = u''.join([soap_request, "<tes:Impuesto>002</tes:Impuesto>"]).encode('UTF-8', errors='replace')
                soap_request  = u''.join([soap_request, "<tes:TasaOCuota>",str( '{0:.6f}'.format(impuestos.amount / 100)),"</tes:TasaOCuota>"]).encode('UTF-8', errors='replace')
                soap_request  = u''.join([soap_request, "<tes:TipoFactor>Tasa</tes:TipoFactor>"]).encode('UTF-8', errors='replace')
                soap_request  = u''.join([soap_request, "</tes:TrasladoConceptoR>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "</tes:Traslados>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "</tes:Impuestos>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:NoIdentificacion>",str(line.product_id.default_code),"</tes:NoIdentificacion>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:Unidad>",str(line.uom_id.name),"</tes:Unidad>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:ValorUnitario>",str(descuento_unidad),"</tes:ValorUnitario>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "</tes:ConceptoR>"]).encode('UTF-8', errors='replace')
        
        soap_request  = u''.join([soap_request, "</tes:Conceptos>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:CondicionesDePago>",(self.payment_term_id.name or ''),"</tes:CondicionesDePago>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Emisor>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Nombre>",company.name,"</tes:Nombre>"]).encode('UTF-8', errors='replace')
        
        soap_request  = u''.join([soap_request, "<tes:RegimenFiscal>",str(company.c_regimenfiscal.name),"</tes:RegimenFiscal>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tes:Emisor>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Folio>",str(self.number),"</tes:Folio>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:FormaPago>",self.c_formapago.name,"</tes:FormaPago>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:LugarExpedicion>",str(company.c_codigopostal.name),"</tes:LugarExpedicion>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:MetodoPago>",str(self.c_metodopago.name),"</tes:MetodoPago>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Moneda>",str(self.currency_id.name),"</tes:Moneda>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Receptor>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Nombre>",str.strip(str(self.partner_id.name).encode('UTF-8', errors='replace')),"</tes:Nombre>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Rfc>",str(self.partner_id.vat),"</tes:Rfc>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:UsoCFDI>",str(self.c_usocfdi.name),"</tes:UsoCFDI>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tes:Receptor>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Referencia>A",str(self.number),"</tes:Referencia>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Serie>A</tes:Serie>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:SubTotal>",str(self.amount_untaxed),"</tes:SubTotal>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:TipoCambio>1</tes:TipoCambio>"]).encode('UTF-8', errors='replace')
        #soap_request  = ''.join([soap_request, "<tes:Descuento>",str(descuento_total),"</tes:Descuento>"])
        soap_request  = u''.join([soap_request, "<tes:Total>",str(self.amount_total),"</tes:Total>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tem:cfdi>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tem:GenerarCFDI>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</soapenv:Body>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</soapenv:Envelope>"]).encode('UTF-8', errors='replace')
        
        url = self.obtiene_url()
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
        carpetas = self.obtener_carpeta_dia()
        nombre_archivo_factura = ''.join([str(self.id),"-",self.partner_id.vat])
        self.guardar_archivo(data,''.join([carpetas['solicitudes'],'/SolicitudWS-',nombre_archivo_factura,'.xml']),"wb")

        try: r = urllib2.urlopen(req,context=ctx)
        except urllib2.URLError as e:
            _logger.info("ERROR")
            _logger.info(e.reason)
            raise Warning(_(u''.join([u'Error al emitir CFDI: ', e.reason])))

          
        xml_respuesta = r.read()
        self.guardar_archivo(xml_respuesta,''.join([carpetas['solicitudes'],'/RespuestaWS-',nombre_archivo_factura,'.xml']),"wb")

        root = ET.fromstring(xml_respuesta)
        for elem in root.getiterator():
            if(self.normalize(elem.tag) == 'OperacionExitosa'):
                operacion_exitosa = elem.text
            if(self.normalize(elem.tag) == 'ErrorDetallado'):
                ErrorDetallado = elem.text
            if(self.normalize(elem.tag) == 'ErrorGeneral'):
                ErrorGeneral = elem.text
            if(self.normalize(elem.tag) == 'PDF'):
                PDF = elem.text
            if(self.normalize(elem.tag) == 'XML'):
                XML = elem.text
        #4 en produccion y 6 en desarrollo
        OperacionExitosa = operacion_exitosa
        _logger.info(self.array_offset)
        _logger.info(OperacionExitosa)
        if(OperacionExitosa=="true"):
            #XML = root[0][0][0][6 + self.array_offset].text
            self.guardar_archivo(XML,''.join([carpetas['xml'],'/',nombre_archivo_factura,'.xml']),"w")
            self.guarda_adjunto(nombre_archivo_factura + '.xml',XML,'text/xml' )
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
            #ErrorDetallado = root[0][0][0][2].text
            #ErrorGeneral = root[0][0][0][3].text
            _logger.info('Error en emision de CFDI')
            _logger.info(ErrorGeneral)
            self.error_cfdi = ErrorGeneral
            self.error_cfdi_detalle = ErrorDetallado
            self.estado_cfdi = 'error'