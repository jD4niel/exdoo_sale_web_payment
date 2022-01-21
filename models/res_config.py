# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"
    
    generate_invoice_on_confirm = fields.Boolean('Generate Invoice?', help="Generate invoice when confirm sale quotation")

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    generate_invoice_on_confirm = fields.Boolean(related="company_id.generate_invoice_on_confirm", readonly=False)
    

