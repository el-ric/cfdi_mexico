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




class AccountPayment(models.Model):
    _inherit = 'account.payment'
    array_offset = 0
    estado_cfdi = fields.Selection([
            ('no_enviado','No enviado'),
            ('procesando','Procesando'),
            ('valido','Factura emitida'),
            ('error','ERROR AL FACTURAR'),
            ('cancelado','Cancelado'),
            ('en_espera','En espera'),]
        ,'CFDI - Estado facturacion', select=True, required=True, default='no_enviado', copy=False)
    mensaje_cfdi = fields.Char('Mensaje PAC',readonly=True, size=500, default='', copy=False)
    uuid_pago = fields.Char('Folio oficial UUID',readonly=True, size=500, default='', copy=False)
    fecha_ultimo_cfdi = fields.Datetime('Fecha ultimo movimiento con PAC', copy=False)
    c_formapago = fields.Many2one('catalogos.sat.c_formapago', 'Forma de pago SAT',ondelete = 'Cascade')
    error_cfdi = fields.Char('Error CFDI',readonly=True, size=5000, default='', copy=False)
    error_cfdi_detalle = fields.Char('Error CFDI detalles',readonly=True, size=5000, default='', copy=False)
    sello = fields.Text('Sello CFDI',readonly=True, default='', copy=False)
    


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
        'res_model': 'account.payment',
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
        soap_request  = ''.join([soap_request, "    <tem:uuid>", self.uuid_pago ,"</tem:uuid>"])
        soap_request  = ''.join([soap_request, "    <tem:email>", self.partner_id.email or 'void@mail.com' ,",", company.email_emisor,"</tem:email>"])
        soap_request  = ''.join([soap_request, "    <tem:titulo>", company.name, " Pago: ", self.name  ,"</tem:titulo>"])
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
    def obtiene_pdf(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
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
        soap_request  = ''.join([soap_request, "<tem:uuid>", self.uuid_pago ,"</tem:uuid>"])
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
            self.guardar_archivo(pdf_contenido,''.join([carpetas['pdf'],'/PDFPago-',nombre_archivo_factura,'.pdf']),"wb")
            #self.guardar_archivo(data,''.join([carpetas['pdf'],'/RequestPDF-',nombre_archivo_factura,'.xml']),"w")
            self.guarda_adjunto(nombre_archivo_factura + '.pdf',pdf_contenido,'application/x-pdf' )

    @api.multi
    def emite_cfdi(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        if self.state != 'posted':
            raise Warning(_('Pago no validada, no es posible emitir factura electronica.'))
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

        soap_request  = ''.join([soap_request, "<tes:ClaveCFDI>CPA</tes:ClaveCFDI>"])

        soap_request  = u''.join([soap_request, "<tes:Conceptos>"])
        soap_request  = u''.join([soap_request, "<tes:ConceptoR>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Cantidad>1</tes:Cantidad>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:ClaveProdServ>84111506</tes:ClaveProdServ>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:ClaveUnidad>ACT</tes:ClaveUnidad>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Descripcion>Pago</tes:Descripcion>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Importe>0</tes:Importe>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:ValorUnitario>0</tes:ValorUnitario>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tes:ConceptoR>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tes:Conceptos>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Emisor>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Nombre>",company.name,"</tes:Nombre>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:RegimenFiscal>",str(company.c_regimenfiscal.name),"</tes:RegimenFiscal>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tes:Emisor>"]).encode('UTF-8', errors='replace')
        #soap_request  = u''.join([soap_request, "<tes:Folio>",str(self.name),"</tes:Folio>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:LugarExpedicion>",str(company.c_codigopostal.name),"</tes:LugarExpedicion>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Moneda>XXX</tes:Moneda>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Pagos>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Pago>"]).encode('UTF-8', errors='replace')
        for pago in self.invoice_ids:
            
            soap_request  = u''.join([soap_request, "<tes:PagosPagoR>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:DoctoRelacionado>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:PagosPagoDoctoRelacionadoR>"]).encode('UTF-8', errors='replace')

            soap_request  = u''.join([soap_request, "<tes:Folio>",str(pago.id),"</tes:Folio>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:IdDocumento>",str(pago.uuid_factura),"</tes:IdDocumento>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:ImpPagado>", str(self.amount),"</tes:ImpPagado>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:ImpSaldoAnt>", str(pago.amount_total) ,"</tes:ImpSaldoAnt>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:ImpSaldoInsoluto>0</tes:ImpSaldoInsoluto>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:MetodoDePagoDR>", str(pago.c_metodopago.name),"</tes:MetodoDePagoDR>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:MonedaDR>MXN</tes:MonedaDR>"]).encode('UTF-8', errors='replace')      
            soap_request  = u''.join([soap_request, "<tes:NumParcialidad>1</tes:NumParcialidad>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:Serie>A</tes:Serie>"]).encode('UTF-8', errors='replace')
            
            soap_request  = u''.join([soap_request, "</tes:PagosPagoDoctoRelacionadoR>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "</tes:DoctoRelacionado>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:FechaPago>", str(self.payment_date),"T12:00:00</tes:FechaPago>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:FormaDePagoP>", self.c_formapago.name ,"</tes:FormaDePagoP>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:MonedaP>MXN</tes:MonedaP>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "<tes:Monto>", str(self.amount),"</tes:Monto>"]).encode('UTF-8', errors='replace')
            soap_request  = u''.join([soap_request, "</tes:PagosPagoR>"]).encode('UTF-8', errors='replace')
            
        soap_request  = u''.join([soap_request, "</tes:Pago>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tes:Pagos>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Receptor>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Nombre>",str.strip(str(self.partner_id.name).encode('UTF-8', errors='replace')),"</tes:Nombre>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Rfc>",str(self.partner_id.vat),"</tes:Rfc>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:UsoCFDI>P01</tes:UsoCFDI>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "</tes:Receptor>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Referencia>",str(self.communication),"</tes:Referencia>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Serie>A</tes:Serie>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:SubTotal>0</tes:SubTotal>"]).encode('UTF-8', errors='replace')
        soap_request  = u''.join([soap_request, "<tes:Total>0</tes:Total>"]).encode('UTF-8', errors='replace')
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
        self.guardar_archivo(data,''.join([carpetas['solicitudes'],'/SolicitudPago-',nombre_archivo_factura,'.xml']),"wb")

        try: r = urllib2.urlopen(req,context=ctx)
        except urllib2.URLError as e:
            _logger.info("ERROR")
            _logger.info(e.reason)
            raise Warning(_(u''.join([u'Error al emitir CFDI: ', e.reason])))

          
        xml_respuesta = r.read()
        self.guardar_archivo(xml_respuesta,''.join([carpetas['solicitudes'],'/RespuestaPago-',nombre_archivo_factura,'.xml']),"wb")

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
        OperacionExitosa = operacion_exitosa
        _logger.info(self.array_offset)
        _logger.info(OperacionExitosa)
        if(OperacionExitosa=="true"):
            #XML = root[0][0][0][6 + self.array_offset].text
            self.guardar_archivo(XML,''.join([carpetas['xml'],'/',nombre_archivo_factura,'.xml']),"w")
            self.guarda_adjunto(nombre_archivo_factura + '.xml',XML,'text/xml' )
            xml_cfdi = ET.fromstring(XML)
            uuid = ''
            for elem in xml_cfdi.getiterator():
               if(self.normalize(elem.tag) == 'TimbreFiscalDigital'):
                    uuid = elem.attrib['UUID']
            sello = xml_cfdi.attrib['Sello']
            #uuid = xml_cfdi[3][1].attrib['UUID']
            self.uuid_pago = uuid
            self.estado_cfdi = 'valido'
            self.mensaje_cfdi = 'Pago emitida'
            self.sello = sello
            self.fecha_ultimo_cfdi = fields.Datetime.now()
            self.envia_email()
            self.obtiene_pdf()

        else:

            _logger.info('Error en emision de CFDI')
            _logger.info(ErrorGeneral)
            self.error_cfdi = ErrorGeneral
            self.error_cfdi_detalle = ErrorDetallado
            self.estado_cfdi = 'error'