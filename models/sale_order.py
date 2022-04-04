# -*- coding: utf-8 -*-
from odoo import fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    generated_link = fields.Boolean('Ya se encuentra pagado')

    def action_confirm(self):
        print("\n ==== action confirm =====\n")
        # Inherits action_done and set auto invoice 
        res = super(SaleOrder,self).action_confirm()
        # Checks auto invoice configuration
        for order in self:
            if order:
                link_wizard = self.env['payment.link.wizard'].sudo().with_context(dict(active_id=order.id)).create({'res_id': order.id})
                link = link_wizard.sudo()._generate_link()
                message = _(f"URL para pagar la venta: <a href='{link}' rel='noopener noreferrer' target='_blank'> {order.name} </a>")
                order.message_post(body=message)

        return res

class AccountMove(models.Model):
    _inherit = 'account.move'

