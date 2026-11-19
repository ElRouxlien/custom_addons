from odoo import fields, models


class BikeRentalReturn(models.TransientModel):
    # TransientModel : un modèle temporaire. Ses enregistrements servent le
    # temps de la fenêtre, puis Odoo les efface tout seul.
    _name = 'bike.rental.return'
    _description = "Assistant de retour d'un vélo"

    # Le contrat concerné. Il est rempli automatiquement à l'ouverture de la
    # fenêtre, grâce au contexte default_rental_id passé par le bouton.
    rental_id = fields.Many2one('bike.rental', string="Contrat", required=True)

    note = fields.Text(string="Observations")
    damage_note = fields.Text(string="Dégâts constatés")
    damage_amount = fields.Float(string="Montant des dégâts")

    def action_validate(self):
        self.ensure_one()
        # 1. Enregistrer l'état des lieux de retour.
        self.env['bike.rental.checkup'].create({
            'rental_id': self.rental_id.id,
            'type': 'return',
            'note': self.note,
            'damage_note': self.damage_note,
            'damage_amount': self.damage_amount,
        })
        # 2. Passer le contrat à l'état "Rendu".
        self.rental_id.action_return()
        # 3. S'il y a des dégâts, préparer leur facture.
        if self.damage_amount:
            self.rental_id.action_create_damage_invoice()
        # Fermer la fenêtre.
        return {'type': 'ir.actions.act_window_close'}
