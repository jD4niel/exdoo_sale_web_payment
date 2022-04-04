# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    
    mercadopago_public_key = fields.Text(u'LLave publica', help=u"Este token es de su cuenta de mercadopago.")
    mercadopago_access_token = fields.Text(u'Token de Acceso', help=u"Este token es de su cuenta de mercadopago.")

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    mercadopago_public_key = fields.Text(related="company_id.mercadopago_public_key", readonly=False)
    mercadopago_access_token = fields.Text(related="company_id.mercadopago_access_token", readonly=False)
    

