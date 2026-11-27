from odoo import fields, models
from odoo.exceptions import AccessError, UserError


class BiblioPurchaseRequest(models.Model):
    _name = 'biblio.purchase.request'
    _description = "Demande d'achat de livre"
    _order = 'date desc, id desc'

    name = fields.Char('Livre demandé', required=True)
    reason = fields.Char('Pourquoi ce livre ?')
    price = fields.Float('Prix estimé')
    librarian_id = fields.Many2one('res.users', string='Bibliothécaire', default=lambda self: self.env.user)
    date = fields.Date('Date', default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Envoyée'),
        ('to_approve', 'À valider'),
        ('done', 'Commandée'),
    ], string='État', default='draft', required=True, readonly=True)
    notes = fields.Text('Notes')

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_order(self):
        """Bouton « Commander » : tout bibliothécaire peut le faire,
        mais la demande part en validation au lieu d'être commandée."""
        if self.filtered(lambda r: r.state != 'submitted'):
            raise UserError("Seule une demande envoyée peut être commandée.")
        self.write({'state': 'to_approve'})

    def action_done(self):
        """Bouton « Valider » : passage en « Commandée », réservé aux responsables.

        Cacher le bouton dans la vue (groups=) ne protège rien : la méthode peut
        être appelée par l'API ou le shell. La vraie sécurité est ce test côté serveur.
        """
        if not self.env.user.has_group('biblio_achats.group_biblio_manager'):
            raise AccessError("Seul un responsable peut valider une demande d'achat.")
        if self.filtered(lambda r: r.state != 'to_approve'):
            raise UserError("Seule une demande à valider peut être validée.")
        self.write({'state': 'done'})
