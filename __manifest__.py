{
    "name": "Real Estate",
    "version": "1.0",
    "category": "Real Estate",
    "summary": "Manage Real Estate properties and transactions",
    "description": """
        A module to manage real estate properties, buyers, and offers.
    """,
    "depends": ["base", "account"],
    "data": [
        "views/estate_property_views.xml",
        "views/estate_property_type_views.xml",
        "views/estate_property_tag_views.xml",
        "views/estate_property_offer_views.xml",
        "views/res_users_view.xml",
        "security/ir.model.access.csv",  
    ],
    'image_1920': '/estate/static/description/icon.png',  # Add logo path here
    'assets': {
        'web.assets_backend': [
            'estate/static/src/css/menu_styles.css',
            # 'estate/static/src/css/estate_kanban.css',

        ],
    },
    "license": "LGPL-3",
    "application": True,
    "installable": True,
}
