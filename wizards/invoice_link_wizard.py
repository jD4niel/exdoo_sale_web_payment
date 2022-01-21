# -*- coding: utf-8 -*-
import hashlib
import hmac
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr, consteq, float_compare


class InvoiceLinkWizard(models.TransientModel):
    _name = "invoice.link.wizard"
    _description = "Generate Invoice Link"

    @api.model
    def default_get(self, fields):
        res = super(InvoiceLinkWizard, self).default_get(fields)
        res_id = self._context.get('active_id')
        res.update({'res_id': res_id,})

        sale_id = self.env['sale.order'].browse(int(res_id))
        if sale_id:
            res.update({'is_already_invoiced': sale_id.invoice_ids.filtered(lambda x: x.state not in ('cancel','draft'))})
            if sale_id.invoice_ids.filtered(lambda x: x.state not in ('draft','cancel')):
                raise UserError(_("This sale is already invoiced!"))
        return res
    

    res_id = fields.Integer('Related Document ID', required=True)
    access_token = fields.Char(compute='_compute_values')
    company_id = fields.Many2one('res.company', compute='_compute_company')
    link = fields.Char(string='Invoice Link', compute='_compute_values')
    is_already_invoiced = fields.Boolean('Is already invoiced')


    @api.depends('access_token','company_id')
    def _compute_values(self):
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        for invoice_link in self:
            sale = self.env['sale.order'].browse(invoice_link.res_id or self._context.get('active_id'))
            token_str = '%s%s%s' % (int(sale.id), int(sale.partner_id.id), int(sale.currency_id.id))
            invoice_link.access_token = hmac.new(secret.encode('utf-8'), token_str.encode('utf-8'), hashlib.sha256).hexdigest()
        # must be called after token generation, obvsly - the link needs an up-to-date token
        self.link = self._generate_link()

    @api.depends('res_id')
    def _compute_company(self):
        for link in self:
            record = self.env['sale.order'].browse(link.res_id)
            link.company_id = record.company_id if 'company_id' in record else False

    def _generate_link(self):
        invoice_link = self
        record = self.env['sale.order'].browse(invoice_link.res_id)
        link = ('%s/web_sale/invoice?order_id=%s&access_token=%s') % (
                    record.get_base_url(),
                    invoice_link.res_id,
                    invoice_link.access_token
                )
        if invoice_link.company_id:
            link += '&company_id=%s' % invoice_link.company_id.id
        return link

    @api.model
    def check_token(self, access_token, sale_id, partner_id, currency_id):
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        token_str = '%s%s%s' % (sale_id, partner_id, currency_id)
        correct_token = hmac.new(secret.encode('utf-8'), token_str.encode('utf-8'), hashlib.sha256).hexdigest()
        if consteq(ustr(access_token), correct_token):
            return True
        return False