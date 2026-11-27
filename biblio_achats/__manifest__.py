{
    'name': "Médiathèque — demandes d'achat",
    'summary': "Exercice à rendre du chapitre 9 : la sécurité",
    'version': '19.0.1.0.0',
    'category': 'Training',
    'author': 'HELB — Cours ERP',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        # Les groupes et les règles d'abord : le CSV des droits d'accès utilise les groupes.
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/request_views.xml',
        'data/request_data.xml',
    ],
    'application': True,
}
