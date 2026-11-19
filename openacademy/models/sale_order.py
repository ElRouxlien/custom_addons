from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    session_id = fields.Many2one('openacademy.session', string='Session de formation')