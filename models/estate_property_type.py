from odoo import models, fields, api


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Type"
    _order = "name asc"

    name = fields.Char(required=True, string="Property Type")
    property_ids = fields.One2many(
        "estate.property", "property_type_id", string="Properties"
    )
    offer_ids = fields.One2many(
        "estate.property.offer", "property_type_id", string="Offers"
    )
    offer_count = fields.Integer(string="Offer Count", compute="_compute_offer_count")

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    _sql_constraints = [
        ("unique_type_name", "unique(name)", "The property type name must be unique.")
    ]

    # In estate_property_type.py
    def action_open_offers(self):
        return {
            "name": "Property Offers",
            "type": "ir.actions.act_window",
            "res_model": "estate.property.offer",
            "view_mode": "tree,form",
            "domain": [("property_type_id", "=", self.id)],
            "context": {
                "default_property_type_id": self.id,
                "search_default_property_type_id": self.id,
            },
        }
