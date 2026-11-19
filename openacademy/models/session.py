from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


class Session(models.Model):
    _name = 'openacademy.session'
    _description = 'OpenAcademy Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    duration = fields.Integer(string="Duration")
    course_id = fields.Many2one('openacademy.course')
    level = fields.Selection(related='course_id.level')

    teacher_id = fields.Many2one(
        'res.partner',
        string='Professeur',
        domain=[('is_instructor', '=', True)],
        tracking=True,
    )
    contact_ids = fields.Many2many(
        'res.partner',
        relation='openacademy_session_partner_rel',
        column1='session_id',
        column2='partner_id',
        string='Participants',
    )
    sale_order_ids = fields.One2many('sale.order', 'session_id', string='Commandes')

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        "Le nom de la session doit être unique.",
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string="State", default='draft', required=True, tracking=True)


    def action_confirm(self):
        for session in self:
            if session.state != 'draft':
                raise UserError("Seule une session en brouillon peut être confirmée.")
            session.state = 'confirm'
        return True

    def action_done(self):
        for session in self:
            if session.state != 'confirm':
                raise UserError("Seule une session confirmée peut être terminée.")
            session.state = 'done'
        return True

    def action_cancel(self):
        for session in self:
            if session.state == 'done':
                raise UserError("Une session terminée ne peut pas être annulée.")
            session.state = 'cancel'
        return True

    def action_set_draft(self):
        for session in self:
            session.state = 'draft'
        return True

    def copy(self, default=None):
        new_sessions = self.browse()
        for session in self:
            vals = dict(default or {})
            if 'name' not in vals:
                vals['name'] = session._get_copy_name()
            new_sessions |= super(Session, session).copy(vals)
        return new_sessions

    def _get_copy_name(self):
        name = f"{self.name} (copie)"
        counter = 2
        while self.search_count([('name', '=', name)]):
            name = f"{self.name} (copie {counter})"
            counter += 1
        return name

