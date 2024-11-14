{
    'name': 'Fusion Sync',
    'version': '0.1.8',
    'author': 'Jaco',
    'company': 'Jacotech',
    'license': 'AGPL-3',
    'depends': ['base', 'mrp'],
    'installable': True,
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'data/fusion_component_sequence.xml',
        'views/fusion_component_views.xml',
        'views/fusion_user_views.xml',
        'views/fusion_component_version_views.xml',
        'views/fusion_component_version_assembly_line_views.xml',
        'views/fusion_menus.xml',
    ],
}
