# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"
    
    generate_invoice_on_confirm = fields.Boolean('Generate Invoice?', help="Generate invoice when confirm sale quotation")
    token_life_days = fields.Integer(u'Días de vida del token', default=1, required=True)
    overdue_message = fields.Text(u'Mensaje de expiración', default=u"Este token ha expirado, consulte a su administrador para gestionar otro.")

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    generate_invoice_on_confirm = fields.Boolean(related="company_id.generate_invoice_on_confirm", readonly=False)
    token_life_days = fields.Integer(related="company_id.token_life_days", readonly=False)
    overdue_message = fields.Text(related="company_id.overdue_message", readonly=False)
    

