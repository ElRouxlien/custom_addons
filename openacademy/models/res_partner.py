from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_instructor = fields.Boolean(string='Professeur', default=False)
    session_ids = fields.Many2many(
        'openacademy.session',
        relation='openacademy_session_partner_rel',
        column1='partner_id',
        column2='session_id',
        string='Sessions suivies',
    )