{
    'name': "Agence Immobilière",
    'summary': "Gestion du catalogue de biens immobiliers",
    'author': "Julien Baron",
    'category': 'Real Estate',
    'version': '19.0.1.0.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_menus.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}