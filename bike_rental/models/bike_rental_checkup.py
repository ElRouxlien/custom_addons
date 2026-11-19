from odoo import fields, models


class BikeRentalCheckup(models.Model):
    _name = 'bike.rental.checkup'
    _description = "État des lieux d'une location"
    _order = 'date'

    # Le contrat auquel appartient cet état des lieux.
    # ondelete='cascade' : si on supprime le contrat, ses états des lieux
    # sont supprimés avec lui.
    rental_id = fields.Many2one('bike.rental', string="Contrat", required=True, ondelete='cascade')

    type = fields.Selection(
        [
            ('departure', "Départ"),
            ('return', "Retour"),
        ],
        string="Type", required=True, default='departure',
    )

    date = fields.Datetime(string="Date", required=True, default=fields.Datetime.now)

    note = fields.Text(string="Observations")

    # Remplis seulement s'il y a des dégâts, en général au retour.
    damage_note = fields.Text(string="Dégâts constatés")
    damage_amount = fields.Float(string="Montant des dégâts")

    # Contrainte en base de données : un seul état des lieux de départ et un
    # seul de retour par contrat.
    _rental_type_unique = models.Constraint(
        'UNIQUE(rental_id, type)',
        "Ce contrat a déjà un état des lieux de ce type.",
    )
