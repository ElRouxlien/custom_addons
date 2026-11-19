from odoo import api, fields, models


class BiblioRoom(models.Model):
    _name = 'biblio.room'
    _description = 'Salle de travail'
    _order = 'name'

    name = fields.Char('Salle', required=True)
    seats = fields.Integer('Places')
    daily_price = fields.Float('Prix par jour', required=True)
    booking_ids = fields.One2many('biblio.room.booking', 'room_id', string='Réservations')
    # Compteur du bouton intelligent : non stocké, recalculé à l'affichage
    booking_count = fields.Integer('Nombre de réservations', compute='_compute_booking_count')

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for room in self:
            room.booking_count = len(room.booking_ids)

    def action_view_bookings(self):
        """Bouton intelligent : ouvre les réservations de cette salle."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Réservations',
            'res_model': 'biblio.room.booking',
            'view_mode': 'list,form',
            # seulement les réservations de CETTE salle
            'domain': [('room_id', '=', self.id)],
            # une réservation créée depuis cette liste a la salle pré-remplie
            'context': {'default_room_id': self.id},
        }


class BiblioRoomBooking(models.Model):
    _name = 'biblio.room.booking'
    _description = "Réservation d'une salle"
    _order = 'start_date desc'

    room_id = fields.Many2one('biblio.room', string='Salle', required=True)
    customer = fields.Char('Réservé par', required=True)
    start_date = fields.Date('Début', required=True, default=fields.Date.context_today)
    end_date = fields.Date('Fin', required=True)
    deposit = fields.Float('Caution')

    # related : le prix vient de la salle, sans être recopié (une seule source de vérité)
    daily_price = fields.Float(related='room_id.daily_price', string='Prix par jour')
    # durée en jours, début et fin compris
    duration = fields.Integer('Durée (jours)', compute='_compute_duration')
    # stocké : on peut trier et totaliser dans la liste
    total_price = fields.Float('Prix total', compute='_compute_total_price', store=True)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for booking in self:
            if booking.start_date and booking.end_date:
                # du 10 au 12 : 2 jours d'écart + 1 car début et fin sont compris = 3 jours
                booking.duration = (booking.end_date - booking.start_date).days + 1
            else:
                # chaque enregistrement doit recevoir une valeur
                booking.duration = 0

    # Champ stocké : le @api.depends doit être complet, sinon la valeur en base reste figée.
    # 'room_id.daily_price' -> si le prix de la salle change, les totaux sont recalculés.
    @api.depends('start_date', 'end_date', 'room_id.daily_price')
    def _compute_total_price(self):
        for booking in self:
            booking.total_price = booking.duration * booking.room_id.daily_price

    @api.depends('room_id.name', 'start_date')
    def _compute_display_name(self):
        # Nom affiché partout (fil d'Ariane, listes déroulantes) :
        # « Réservation <salle> – <date de début> »
        for booking in self:
            date_str = booking.start_date.strftime('%d/%m/%Y') if booking.start_date else ''
            booking.display_name = f"Réservation {booking.room_id.name or ''} – {date_str}"

    @api.onchange('room_id')
    def _onchange_room_id(self):
        # Aide à la saisie (formulaire uniquement) : caution proposée = 2 × prix par jour.
        # Ce n'est pas un compute : l'utilisateur peut encore modifier la caution.
        if self.room_id:
            self.deposit = 2 * self.room_id.daily_price
