from odoo import fields, models
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Bien immobilier"

    name = fields.Char(string="Nom du bien", required=True)
    description = fields.Text(string="Description")
    expected_price = fields.Float(string="Prix attendu", required=True)
    selling_price = fields.Float(string="Prix de vente", readonly=True, copy=False)
    date_availability = fields.Date(string="Date de disponibilité")
    active = fields.Boolean(string="Actif", default=True)
    state = fields.Selection(
        [
            ("new", "Nouveau"),
            ("offer_received", "Offre reçue"),
            ("offer_accepted", "Offre acceptée"),
            ("sold", "Vendu"),
            ("canceled", "Annulé"),
        ],
        string="Statut",
        required=True,
        copy=False,
        default="new",
        readonly=True,
    )

    def action_sold(self):
        for record in self:
            if record.state == "canceled":
                raise UserError("Un bien annulé ne peut pas être vendu.")
            record.state = "sold"
        return True

    def action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise UserError("Un bien vendu ne peut pas être annulé.")
            record.state = "canceled"
        return True

    def copy(self, default=None):
        new_records = self.browse()
        for record in self:
            values = dict(default or {})
            values.setdefault("name", f"{record.name} (Copie)")
            values["selling_price"] = 0.0
            values["state"] = "new"
            new_records |= super(EstateProperty, record).copy(values)
        return new_records