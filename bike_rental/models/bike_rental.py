from odoo import Command, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BikeRental(models.Model):
    _name = 'bike.rental'
    _description = "Contrat de location de vélo"
    # Les contrats les plus récents s'affichent en premier.
    _order = 'start_date desc, id desc'

    # ------------------------------------------------------------------
    # Champs
    # ------------------------------------------------------------------

    # Référence du contrat. Elle vaut "Nouveau" tant que le contrat n'est pas
    # enregistré, puis la séquence la remplace (voir create() plus bas).
    name = fields.Char(string="Référence", default="Nouveau", readonly=True, copy=False)

    partner_id = fields.Many2one('res.partner', string="Client", required=True)

    # Le vélo loué est un numéro de série précis, pas un article en général.
    # Il n'est pas obligatoire à la création : une demande arrive sans vélo,
    # le vendeur en choisit un après avoir vérifié la disponibilité.
    # domain : la liste ne propose que les vélos de la flotte de location.
    lot_id = fields.Many2one(
        'stock.lot', string="Vélo (n° de série)",
        domain=[('is_rental_bike', '=', True)],
    )

    warehouse_id = fields.Many2one('stock.warehouse', string="Magasin", required=True)

    start_date = fields.Date(string="Début", required=True, default=fields.Date.context_today)
    end_date = fields.Date(string="Fin", required=True, default=fields.Date.context_today)

    # Champs calculés : Odoo les recalcule tout seul quand les champs listés
    # dans @api.depends changent. store=True les enregistre en base, ce qui
    # permet de trier et de filtrer dessus.
    duration = fields.Integer(string="Durée (jours)", compute='_compute_duration', store=True)

    daily_price = fields.Float(string="Prix par jour")
    amount_total = fields.Float(string="Montant", compute='_compute_amount_total', store=True)

    state = fields.Selection(
        [
            ('draft', "Demande"),
            ('confirmed', "Confirmé"),
            ('rented', "Loué"),
            ('returned', "Rendu"),
            ('cancel', "Annulé"),
        ],
        string="État", default='draft', required=True, copy=False,
    )

    # Les états des lieux du contrat. One2many est l'inverse du Many2one
    # rental_id défini dans bike.rental.checkup.
    checkup_ids = fields.One2many('bike.rental.checkup', 'rental_id', string="États des lieux")

    # Total des dégâts relevés dans les états des lieux.
    damage_total = fields.Float(string="Total des dégâts", compute='_compute_damage_total', store=True)

    # Caution. Texte libre pour l'instant : la nature de la caution
    # (pièce d'identité ?) reste à confirmer avec le client.
    deposit_type = fields.Char(string="Caution laissée")
    deposit_returned = fields.Boolean(string="Caution restituée", copy=False)

    # Les deux factures possibles d'un contrat. Elles sont créées par les
    # boutons, jamais saisies à la main : d'où readonly=True.
    invoice_id = fields.Many2one('account.move', string="Facture de location", readonly=True, copy=False)
    damage_invoice_id = fields.Many2one('account.move', string="Facture des dégâts", readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Champs calculés
    # ------------------------------------------------------------------

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rental in self:
            if rental.start_date and rental.end_date:
                # +1 : une location du lundi au lundi compte pour 1 jour.
                rental.duration = (rental.end_date - rental.start_date).days + 1
            else:
                rental.duration = 0

    @api.depends('duration', 'daily_price')
    def _compute_amount_total(self):
        for rental in self:
            # Prix simple : pas de tarif dégressif (hors périmètre, validé par le client).
            rental.amount_total = rental.duration * rental.daily_price

    @api.depends('checkup_ids.damage_amount')
    def _compute_damage_total(self):
        for rental in self:
            # mapped() renvoie la liste des montants, sum() les additionne.
            rental.damage_total = sum(rental.checkup_ids.mapped('damage_amount'))

    def _has_checkup(self, checkup_type):
        """Renvoie True si le contrat a un état des lieux du type demandé."""
        self.ensure_one()
        return bool(self.checkup_ids.filtered(lambda c: c.type == checkup_type))

    # ------------------------------------------------------------------
    # Contraintes
    # ------------------------------------------------------------------

    @api.constrains('start_date', 'end_date')
    def _check_end_date(self):
        for rental in self:
            if rental.end_date < rental.start_date:
                raise ValidationError("La date de fin ne peut pas précéder la date de début.")

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        # On prend un numéro dans la séquence au moment de l'enregistrement,
        # et pas avant : sinon un numéro serait perdu à chaque formulaire
        # ouvert puis abandonné.
        for vals in vals_list:
            if vals.get('name', "Nouveau") == "Nouveau":
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.rental')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Boutons
    # ------------------------------------------------------------------

    def action_confirm(self):
        for rental in self:
            if rental.state != 'draft':
                raise UserError("Seule une demande peut être confirmée.")
            if not rental.lot_id:
                raise UserError("Choisissez un vélo avant de confirmer la location.")
            rental.state = 'confirmed'

    def action_start(self):
        for rental in self:
            if rental.state != 'confirmed':
                raise UserError("Seule une location confirmée peut démarrer.")
            if not rental._has_checkup('departure'):
                raise UserError("Faites l'état des lieux de départ avant de remettre le vélo.")
            # Sécurité : un même vélo ne peut pas être sorti deux fois.
            already_out = self.search_count([
                ('lot_id', '=', rental.lot_id.id),
                ('state', '=', 'rented'),
                ('id', '!=', rental.id),
            ])
            if already_out:
                raise UserError("Ce vélo est déjà en location.")
            rental.state = 'rented'

    def action_return(self):
        for rental in self:
            if rental.state != 'rented':
                raise UserError("Seul un vélo en location peut être rendu.")
            if not rental._has_checkup('return'):
                raise UserError("Faites l'état des lieux de retour avant de reprendre le vélo.")
            rental.state = 'returned'

    def action_cancel(self):
        for rental in self:
            if rental.state not in ('draft', 'confirmed'):
                raise UserError("Une location démarrée ne peut plus être annulée.")
            rental.state = 'cancel'

    # ------------------------------------------------------------------
    # Facturation
    # ------------------------------------------------------------------

    def _get_service_product(self, code, name):
        """Renvoie l'article de service utilisé sur les factures, en le créant
        la première fois.

        Passer par un article permet à Odoo d'appliquer la TVA et le compte
        comptable réglés sur l'article, comme pour n'importe quelle vente.
        L'article est créé ici et non dans un fichier de données XML : avec la
        boutique en ligne installée, un article créé pendant le chargement du
        module est refusé (un champ obligatoire du site n'est pas encore connu).
        """
        Product = self.env['product.product']
        product = Product.search([('default_code', '=', code)], limit=1)
        if not product:
            product = Product.create({
                'name': name,
                'default_code': code,
                'type': 'service',
                'purchase_ok': False,
            })
        return product

    def _create_invoice(self, product, label, quantity, price_unit):
        """Crée une facture client en brouillon, avec une seule ligne."""
        self.ensure_one()
        return self.env['account.move'].create({
            # out_invoice = facture client (in_invoice serait une facture fournisseur).
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            # Le champ "Origine" de la facture rappelle le contrat.
            'invoice_origin': self.name,
            # Command.create : crée la ligne en même temps que la facture.
            'invoice_line_ids': [Command.create({
                # L'article apporte la TVA et le compte comptable.
                'product_id': product.id,
                'name': label,
                'quantity': quantity,
                'price_unit': price_unit,
            })],
        })

    def action_create_invoice(self):
        for rental in self:
            if rental.state not in ('confirmed', 'rented', 'returned'):
                raise UserError("Confirmez la location avant de la facturer.")
            if rental.invoice_id:
                raise UserError("Cette location est déjà facturée.")
            label = "Location du vélo %s du %s au %s" % (
                rental.lot_id.name,
                rental.start_date.strftime('%d/%m/%Y'),
                rental.end_date.strftime('%d/%m/%Y'),
            )
            # Une ligne : nombre de jours x prix par jour.
            product = rental._get_service_product('LOC-VELO', "Location de vélo")
            rental.invoice_id = rental._create_invoice(product, label, rental.duration, rental.daily_price)

    def action_create_damage_invoice(self):
        for rental in self:
            if rental.state != 'returned':
                raise UserError("Les dégâts se facturent après le retour du vélo.")
            if not rental.damage_total:
                raise UserError("Aucun dégât n'a été relevé sur ce contrat.")
            if rental.damage_invoice_id:
                raise UserError("Les dégâts de cette location sont déjà facturés.")
            label = "Dégâts constatés au retour du vélo %s (contrat %s)" % (rental.lot_id.name, rental.name)
            product = rental._get_service_product('LOC-DEGATS', "Dégâts sur vélo de location")
            rental.damage_invoice_id = rental._create_invoice(product, label, 1, rental.damage_total)
