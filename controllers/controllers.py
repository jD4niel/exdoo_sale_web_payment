# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, _, exceptions
from odoo.http import request
from datetime import datetime
import pytz
import mercadopago


class SaleWebPayment(http.Controller):      
    

    @http.route(['/sale_order/payment'], type='http', auth='public', website=True, sitemap=False)
    def index(self, order_id=None, access_token=None, company_id=None, **kw):
        env = request.env
        if not order_id and not access_token:
            raise werkzeug.exceptions.NotFound

        sale = env['sale.order'].sudo().browse(int(order_id))
        partner_id = env['res.partner'].sudo()

        company = sale.company_id
        if company_id and not sale.company_id:
            company = env['res.company'].browse(int(company_id))

        # Agrega credenciales
        mp_access_token = sale.company_id.mercadopago_access_token
        if not mp_access_token:
            raise werkzeug.exceptions.NotFound

        sdk = mercadopago.SDK(mp_access_token)
        #sdk = mercadopago.SDK("TEST-7672996189096229-033113-154f63e10177c834d66b62e884aede54-1099000078")

        preference_data = {
            "items": [
                {
                    "title": "Orden: " + sale.display_name,
                    "quantity": 1,
                    "unit_price": sale.amount_total,
                }
            ],
        }


        preference_response = sdk.preference().create(preference_data)
        print("preference_response: ", preference_response)
        preference = preference_response["response"] 
       
        if not preference:
            preference = dict()

        if sale and access_token:
            if not sale:
                raise werkzeug.exceptions.NotFound
            partner_id = sale.partner_id

            
            # Verificar la validez del token
            token_ok = env['payment.link.wizard'].sudo().check_token(access_token, int(order_id), int(sale.partner_id.id), int(sale.currency_id.id))
            if not token_ok:
                raise werkzeug.exceptions.NotFound

        values = {
            'token': access_token,
            'order_id': sale,
            'partner_id': partner_id,}

        if preference_response.get('status','') == "approved":
            values.update({
                'preference': preference,
                'ky': sale.company_id.mercadopago_public_key,
            })

        else:
            values.update({'error': f"Error {preference_response.get('status','')} - {preference_response.get('response','')} "})

        print("preference: %s"%preference)
        return request.render('exdoo_sale_web_payment.index', values)
 
   