# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import UserError
from datetime import datetime, timezone
import pytz

class SaleOrder(models.Model):
    _inherit = "sale.order"

    generated_link = fields.Boolean('Is already invoiced')

    def action_sale_invoice_from_web(self,partner_id=False):
        # Facturar el pedido de pos desde website
        self.env.user = self.env['res.users'].browse(2)
        moves = self.env['account.move'].sudo()

        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.invoice_ids:
                moves += order.invoice_ids
                continue

            move_vals = order.sudo()._prepare_invoice_vals()
            if partner_id:
                move_vals.update({'partner_id': partner_id})
            new_move = moves.sudo()\
                            .with_company(order.company_id)\
                            .with_context(default_move_type=move_vals['move_type'])\
                            .create(move_vals)
            message = _("This invoice has been created from website using sale_auto_invoice: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a>xs") % (order.id, order.name)
            new_move.message_post(body=message)
            order.write({'invoice_ids': (4,0,new_move.id)})
            new_move.sudo().with_company(order.company_id)._post()

            attachment_ids = self.env['ir.attachment'].sudo().search([('res_model', '=', 'account.move'),('res_id','=',new_move.id)])
            attachment_ids.sudo().write({'public': True})
            moves += new_move

        return moves

    def _prepare_invoice_vals(self):
        self.ensure_one()
        invoice_vals = self._prepare_invoice()
        invoice_line_vals = []
        invoice_item_sequence = 0
        for line in self.order_line:
            invoice_line_vals.append(
                (0, 0, line._prepare_invoice_line(
                    sequence=invoice_item_sequence,
                )),
            )
            invoice_item_sequence += 1

        invoice_vals['invoice_line_ids'] += invoice_line_vals

        return invoice_vals

    def action_confirm(self):
        # Inherits action_done and set auto invoice 
        res = super(SaleOrder,self).action_confirm()
        # Checks auto invoice configuration
        for order in self:
            if order and order.company_id.generate_invoice_on_confirm:
                link_wizard = self.env['invoice.link.wizard'].sudo().with_context(dict(active_id=order.id)).create({'res_id': order.id})
                link = link_wizard.sudo()._generate_link()
                message = _(f"URL para generar factura: <a href='{link}' rel='noopener noreferrer' target='_blank'> {order.name} </a>")
                order.message_post(body=message)

        return res

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_cfdi_from_web_sale(self, web_values):
        self.env.user = self.env['res.users'].browse(2)
        for move in self.sudo():
            # Comprobamos que exista el modulo cfdi_33 y luego creamos el wizard para timbrar cfdi
            experts_account_invoice_cfdi_33  = self.env['ir.module.module'].sudo().search([('name', '=', 'experts_account_invoice_cfdi_33')])
            if experts_account_invoice_cfdi_33  and experts_account_invoice_cfdi_33.state == 'installed':
                try:
                    if self.date_invoice_tz:
                        datetime_inv_tz = self.date_invoice_tz
                    else:
                        tz_name = pytz.timezone('Mexico/General')
                        datetime_inv_tz = self.invoice_datetime.astimezone(tz_name)
                        self.date_invoice_tz = datetime_inv_tz
                except:
                    pass

                if self.move_type == 'out_refund':
                    if not self.invoice_advanced_rel_ids and not self.invoice_manual_rel_ids:
                        raise UserError (_('Error! \n No puedes timbrar una Nota de credito si no esta relacionada a una factura. Agregue una factura en la pestaña CFDI -> Documentos Relacionados para timbrarla.'))
                cfdi_vals = {
                    'cfdi_partner_id': self.partner_id.id,
                    'uso_cfdi_id': web_values.get('uso_cfdi_id'),
                    'met_pago_id': web_values.get('pay_method_id'),
                    'forma_pago_id': web_values.get('pay_forma_id'),
                }
                # move.sudo().write(cfdi_vals)
                move.sudo().create_cfdi()
                # vals = {
                #     'invoice_id':self.id,
                #     'partner_id':self.partner_id.id,
                #     'zip':self.partner_id.zip,
                #     'street2': self.partner_id.street2 or '',
                #     'street': self.partner_id.street or '',
                #     'l10n_mx_street3': self.partner_id.l10n_mx_street3,
                #     'l10n_mx_street4': self.partner_id.l10n_mx_street4,
                #     'l10n_mx_city2': self.partner_id.l10n_mx_city2,
                #     'city': self.partner_id.city,
                #     'state_id': self.partner_id.state_id.id,
                #     'country_id': self.partner_id.country_id.id,
                #     'email': self.partner_id.email,
                    
                # }
                # vals.update(web_values)
                # wizard_id = self.env['partner.invoice.wizard'].sudo().create(vals)
                # wizard_id.sudo().create_cfdi()

                return self
    
    