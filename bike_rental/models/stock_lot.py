from odoo import api, fields, models


class StockLot(models.Model):
    # _inherit sans _name : on n'invente pas un nouveau modèle, on ajoute des
    # champs au modèle "numéro de série" qui existe déjà dans Odoo.
    _inherit = 'stock.lot'

    # Case à cocher : ce vélo fait partie de la flotte de location.
    is_rental_bike = fields.Boolean(string="Vélo de location")

    # Tous les contrats de ce vélo (l'inverse du champ lot_id de bike.rental).
    rental_ids = fields.One2many('bike.rental', 'lot_id', string="Contrats de location")

    # Disponible ou loué : calculé d'après les contrats, jamais saisi à la main.
    rental_state = fields.Selection(
        [
            ('available', "Disponible"),
            ('rented', "Loué"),
        ],
        string="Statut de location", compute='_compute_rental_state', store=True,
    )

    @api.depends('rental_ids.state')
    def _compute_rental_state(self):
        for lot in self:
            # Le vélo est loué si au moins un de ses contrats est à l'état "Loué".
            if lot.rental_ids.filtered(lambda r: r.state == 'rented'):
                lot.rental_state = 'rented'
            else:
                lot.rental_state = 'available'
