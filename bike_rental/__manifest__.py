{
    'name': "Location de vélos",
    'summary': "Contrats de location de vélos en magasin",
    'description': """
Gestion des contrats de location : client, vélo (n° de série), magasin,
période, prix par jour et suivi de l'état du contrat.
    """,
    'author': "Julien, Akim, Nawfal, Ilyas",
    'category': 'Sales',
    'version': '0.1',
    'license': 'LGPL-3',

    # stock apporte les numéros de série (stock.lot), les entrepôts
    # (stock.warehouse) et, par dépendance, les contacts (res.partner).
    # account apporte les factures (account.move).
    'depends': ['stock', 'account'],

    # L'ordre compte : les droits d'abord, puis les données, les vues,
    # et le menu en dernier car il pointe vers l'action définie dans les vues.
    'data': [
        # Les groupes avant le CSV, car le CSV les cite.
        'security/bike_rental_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        # L'assistant avant la fiche du contrat, car un bouton de la fiche l'ouvre.
        'views/bike_rental_return_views.xml',
        'views/bike_rental_views.xml',
        'views/stock_lot_views.xml',
        'views/menus.xml',
    ],

    # application = True : le module apparaît comme une application dans Odoo.
    'application': True,
}
