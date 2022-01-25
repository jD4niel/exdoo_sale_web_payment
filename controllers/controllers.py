# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, _, exceptions
from odoo.http import request


class SaleAutoInvoice(http.Controller):

    def get_moves(self, moves):
        # Return an list of dict with all files
        move_list = []
        attach_obj = request.env['ir.attachment']
        for move in moves:
            val = {'name': move.name, 'id': move.id }
            attachment_id = attach_obj.sudo().search([('res_id','=',move.id),('res_model','=','account.move')])
            if attachment_id:
                pdf_files = attachment_id.filtered(lambda x: 'pdf' in x.mimetype )
                xml_files = attachment_id.filtered(lambda x: 'xml' in x.name )
                if pdf_files:
                    pdf_files.sudo().write({'public': True})
                if xml_files:
                    xml_files.sudo().write({'public': True})
                val.update({'pdf_files': pdf_files})
                val.update({'xml_files': xml_files})
            move_list.append(val)

        return move_list
    
    @http.route('/web_sale/cfdi/submit', type='http', auth='public', website=True, sitemap=False)
    def cfdi_submit(self,  **post):
        """ Esta funcion sirve para crear el cfdi, si no existe el rfc entonces se regresa la misma vista mandando un mensaje de error """

        partner_obj = request.env['res.partner'].sudo()
        order_id = request.env['sale.order'].sudo().browse(int(post.get('order_id',0))) if post.get('order_id',0) else request.env['sale.order'].sudo()
        moves = request.env['account.move'].sudo()

        vat = str(post.get('rfc','')).strip()
        vat_so_search = [vat] if vat else [vat, vat[2:]]
        # Agregamos a la lista el RFC en minusculas y mayúsculas
        vat_so_search.append(vat.lower())
        vat_so_search.append(vat.upper())
        values = {
            'order_id': order_id,
            'partner_id': partner_obj,
        }
        # Se obtiene los modelos uso_cfdi, metodo de pago y forma de pago

        # Si le dieron click al boton de buscar entonces regresa el cliente con sus datos
        partner_id = partner_obj.sudo().search([('vat','in',vat_so_search)],limit=1) or partner_obj.browse(int(post.get('partner_id')))
        partner_search_id = partner_obj.sudo().search([('vat','in',vat_so_search)],limit=1)

        if post.get('search') == 'buscar':
            values.update({'vat': vat or False, 'no_partner': bool(partner_search_id), 'partner_id': partner_id, 'order_id': order_id})
            try:
                values.update(self.get_cfdi_defaults())
                values.update(self.get_cfdi_values())
            except Exception as error:
                pass

            values.update({'create_partner_token': post.get('create_partner_token')})
            if not partner_search_id:
                values.update({'error': "No se encontro RFC: %s en la lista de Clientes."%(vat.upper(),)})
            return request.render("exdoo_sale_auto_invoice.cfdi_from_sale", values)
            
        # cretae custom moves
        #generated_moves = request.env['sale.advance.payment.inv'].with_context(dict(active_ids='jsjsjs')).create_invoices()
        if order_id and partner_id:
            if order_id.sudo().invoice_ids.filtered(lambda move: move.state in ('draft', 'posted')):
                moves = order_id.sudo().invoice_ids.filtered(lambda move: move.state in ('draft', 'posted'))[0]
                if moves.filtered(lambda move: move.state in ('draft')):
                    moves.filtered(lambda move: move.state in ('draft')).sudo().write({'partner_id': partner_id.id})
            else:
                # moves = order_id.sudo().action_sale_invoice_from_web()
                moves = order_id.sudo()._create_invoices()
                moves.sudo().write({'partner_id': partner_id.id})
                if moves:
                    moves.filtered(lambda move: move.state == 'draft').sudo()._post()
            values.update({'moves': self.get_moves(moves)})

        if not self.check_exdoo_invoice_module():
            values.update({'not_exdoo_cfdi_module': True,'move_sign':True})
        else:
            values.update(self.get_cfdi_values())
            if partner_id:
                values.update(self.get_cfdi_defaults(partner_id))
                #if not(partner_id.uso_cfdi_id and partner_id.forma_pago_id and partner_id.met_pago_id):
                #    values.update({'error':'Faltan algunos campos a especificar para poder timbrar la factura!','show_cfdi_data':True})
                values.update({'partner_id': partner_id,'move_sign': False,})
            else:
                values.update(self.get_cfdi_defaults())
                values.update({'move_sign': False,'no_partner': bool(partner_id)})

            # Si existe el pedido y existe el cliente
            if order_id and partner_id and post.get('create_cfdi',False):
                # Creamos la factura y la intentamos timbrar (si es que tiene experts_account_invoice_cfdi_33)
                try:
                    moves.sudo().action_invoice_remission()
                except:
                    pass
                try:
                    partner_cfdi_id = partner_id.uso_cfdi_id.id if partner_id.uso_cfdi_id else False
                    partner_forma_pago_id = partner_id.forma_pago_id.id if partner_id.forma_pago_id else False
                    partner_met_pago_id = partner_id.met_pago_id.id if partner_id.met_pago_id else False

                    uso_cfdi_id = int(post.get('uso_cfdi_id', False)) if post.get('uso_cfdi_id', False) else partner_cfdi_id
                    forma_pago_id = int(post.get('forma_pago_id', False)) if post.get('forma_pago_id', False) else partner_forma_pago_id
                    met_pago_id = int(post.get('met_pago_id', False)) if post.get('met_pago_id', False) else partner_met_pago_id

                    cfdi_values = {
                        'partner_id': partner_id.id,
                        'uso_cfdi_id': uso_cfdi_id,
                        'forma_pago_id': forma_pago_id,
                        'met_pago_id': met_pago_id,
                        'cfdi_partner_id': partner_id.id,
                    }

                    if not moves.sign:
                        #moves.sudo().write(cfdi_values)
                        partner_values = cfdi_values.copy()
                        partner_values.update({
                            'vat': vat,
                            'zip': post.get('zip',False),
                            'email': post.get('email',False),
                        })
                        cfdi_wizard = moves.sudo().create_cfdi_from_web_sale(partner_values)
                        pdf = request.env.ref('experts_account_invoice_cfdi_33.custom_invoice_pdf').sudo()._render_qweb_pdf(moves.ids)[0]
                        # moves.sudo().write(cfdi_values)
                        # moves.sudo().create_cfdi()
                        if cfdi_wizard:
                            values.update({'move_sign': True})
                    else:
                        values.update({'move_sign': True})

                    attachment_ids = request.env['ir.attachment'].sudo().search([('res_model', '=', 'account.move'),('res_id','=',moves.id)])
                    attachment_ids.sudo().write({'public': True})

                except Exception as error:
                    values.update({'cfdi_error':  "Controller error on create cfdi (cfdi_submit) :\n" + str(error)})
                    pass


            if not values.get('vat',False):
                values.update({'vat': vat or False, 'no_partner': bool(partner_id)})
        if moves:
            values.update({'moves': self.get_moves(moves)})
        return request.render("exdoo_sale_auto_invoice.cfdi_from_sale_results", values)
        # return request.render("exdoo_sale_auto_invoice.cfdi_from_sale", values)

    @http.route(['/web_sale/invoice'], type='http', auth='public', website=True, sitemap=False)
    def invoice_from_web(self, order_id=None, access_token=None, company_id=None, partner_external_id=0, partner_created=0, **kw):
        env = request.env
        if not order_id and not access_token:
            raise werkzeug.exceptions.NotFound

        sale = env['sale.order'].sudo().browse(int(order_id))
        partner_id = env['res.partner'].sudo()
        moves = env['account.move'].sudo()
        values = dict()
        if sale and access_token:
            if not sale:
                raise werkzeug.exceptions.NotFound
            partner_id = sale.partner_id

            if int(partner_created):
                if not int(partner_external_id):
                    values.update({'partner_error': 'Ocurrio un error al intentar crear el cliente, intente nuevamente o contacte a su administrador'})
                
                else:
                    partner_id = partner_id.browse(int(partner_external_id)) 
                    if partner_id:
                        values.update({'partner_success': "Se ha creado correctamente el cliente!"})
                    else:
                        values.update({'partner_error': 'No se encontró el cliente correspondiente (id=%s), intente nuevamente o contacte a su administrador'%partner_external_id})

            token_ok = env['payment.link.wizard'].sudo().check_token(access_token, int(order_id), int(sale.partner_id.id), int(sale.currency_id.id))
            if not token_ok:
                raise werkzeug.exceptions.NotFound

            if sale.state == 'invoiced' and sale.invoice_ids:
                moves = sale.invoice_ids.filtered(lambda x: x.sign and x.state not in ['draft','cancel'])
            else:
                # create invoice from sale
                pass

        values.update({
            'move_sign': bool(moves),
            'token': access_token,
            'order_id': sale,
            'partner_id': partner_id,
            'moves': moves,
            'create_partner_token': f'/web_sale/partner?order_id={sale.id}&access_token={access_token}&company_id={company_id}'
        })

        # Se obtiene los modelos uso_cfdi, metodo de pago y forma de pago
        if self.check_exdoo_invoice_module():
            values.update(self.get_cfdi_values())
            if partner_id:
                values.update(self.get_cfdi_defaults(partner_id))
            else:
                values.update(self.get_cfdi_defaults())
            if partner_id and any([partner_id.uso_cfdi_id, partner_id.forma_pago_id, partner_id.met_pago_id]):
                values.update({'show_cfdi_data':True,'info': _('Order has a partner, but it has not all invoice field completed.')})
        else:
            values.update({'not_exdoo_cfdi_module': True})

        return request.render('exdoo_sale_auto_invoice.cfdi_from_sale', values)
 
    def get_cfdi_values(self):
        uso_cfdi = request.env['res.uso.cfdi'].sudo().search([])
        forma_pago_id = request.env['res.forma.pago'].sudo().search([])
        pay_method_id = request.env['res.met.pago'].sudo().search([])

        return {
            'uso_cfdi_id': uso_cfdi,
            'forma_pago_id': forma_pago_id,
            'met_pago_id': pay_method_id,
        }

    def get_cfdi_defaults(self,partner_id=False):
        # Get default methods
        uso_cfdi = request.env['res.uso.cfdi'].sudo().search([('name','=','G03')],limit=1)
        forma_pago_id = request.env['res.forma.pago'].sudo().search([('name','=','01')],limit=1)
        pay_method_id = request.env['res.met.pago'].sudo().search([('display_name','=','PUE')],limit=1)

        defaults = {
            'default_uso_cfdi_id': uso_cfdi,
            'default_forma_pago_id': forma_pago_id,
            'default_met_pago_id': pay_method_id,
        }
        if partner_id:
            if partner_id.uso_cfdi_id:
                defaults.update({'default_uso_cfdi_id': partner_id.uso_cfdi_id})
            if partner_id.forma_pago_id:
                defaults.update({'default_forma_pago_id': partner_id.forma_pago_id})
            if partner_id.met_pago_id:
                defaults.update({'default_met_pago_id': partner_id.met_pago_id})

        return defaults

    def check_exdoo_invoice_module(self):
        experts_account_invoice_cfdi_33  = request.env['ir.module.module'].sudo().search([('name', '=', 'experts_account_invoice_cfdi_33')])
        exdoo_account_invoice_cfdi_33  = request.env['ir.module.module'].sudo().search([('name', '=', 'exdoo_account_invoice_cfdi_33')])
        # check if module is correct
        return bool((experts_account_invoice_cfdi_33  and experts_account_invoice_cfdi_33.state == 'installed') or (exdoo_account_invoice_cfdi_33 and exdoo_account_invoice_cfdi_33.state == 'installed'))

    @http.route('/web_sale/partner', auth='public', website=True)
    def partner_new(self, order_id=None, access_token=None, company_id=None,**post):
        values = {'token_url': f'order_id={order_id}&access_token={access_token}&company_id={company_id}'}
        try:
            values.update(self.get_cfdi_values())
        except:
            pass
        values.update({'partner': request.env['res.partner'],})

        if post.get('partner_correct'):
            return request.render("exdoo_sale_auto_invoice.cfdi_from_sale", values)
        return request.render("exdoo_sale_auto_invoice.create_partner", values)


    @http.route('/web_sale/partner/save', auth='public', website=True)
    def partner_save(self, **post):
        values = {'partner_id': False }
        token_url = False

        if post:
            token_url = post.get('token_url')
            post.pop('token_url')
            try:
                # Buscamos el RFC 
                vat = str(post.get('vat')).strip()
                vats = [vat.lower(),vat.upper()]

                partner_id = request.env['res.partner'].sudo().search([('vat','in',vats)])
                if not partner_id:
                    country_id = request.env['res.partner'].sudo().env.ref('base.mx').id
                    post.update({'country_id': country_id})
                    post.update({'vat': vat.upper()})
                    partner_id = request.env['res.partner'].sudo().create(post)
                    values.update({'partner_id': partner_id, 'partner_correct': True})
                else:
                    values.update({'error': 'El RFC ingresado ya existe.'})
            except Exception as error:
                values.update({'error': 'Exception error:' + str(error)})
        else:
            values.update({'error': 'No se ingresaron valores en el formulario, intentelo nuevamente.'})
        base_url = request.website.get_base_url()
        if token_url:
            if '&partner_external_id=' in token_url:
                token_url = token_url[:token_url.find('&partner_external_id=')]
            partner_uid = partner_id.id if partner_id else 0
            url = base_url + '/web_sale/invoice?'+token_url+'&partner_external_id=' + str(partner_uid) + '&partner_created=' + str(partner_uid)
            
            if values.get('error'):
                values.update(dict(token_url=token_url+'&partner_external_id=' + str(partner_uid) + '&partner_created=' + str(partner_uid)))
                return request.render("exdoo_sale_auto_invoice.create_partner", values)
            return request.redirect(url)

        return request.render("exdoo_sale_auto_invoice.create_partner", values)
