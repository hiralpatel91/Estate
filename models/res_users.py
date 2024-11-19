from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    # Define the One2many field for properties managed by the user
    property_ids = fields.One2many(
        "estate.property",  # The related model
        "seller_id",  # The inverse field in estate.property that points to the user (salesperson)
        string="Managed Properties",  # Label for the field
        domain=[
            ("status", "in", ["available", "offer_received"])
        ],  # Filter for available properties
    )
