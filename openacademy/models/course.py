from odoo import fields, models

class Course(models.Model):
    _name = "openacademy.course"
    _description = "Openacademy Course"

    name = fields.Char()
    description = fields.Text()
    start_date = fields.Date()
    level = fields.Selection([('easy', 'Easy'), ('middle', 'Middle'), ('hard', 'Hard')])
    rate = fields.Integer()
    session_ids = fields.One2many('openacademy.session', 'course_id')
    responsible_id = fields.Many2one('res.users')