from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError, UserError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "amount desc"

    amount = fields.Float(string="Offer Amount", required=True)
    property_id = fields.Many2one("estate.property", string="Property", required=True)
    partner_id = fields.Many2one("res.partner", string="Buyer", required=True)
    status = fields.Selection(
        [("accepted", "Accepted"), ("refused", "Refused")], string="Status"
    )
    property_type_id = fields.Many2one(
        "estate.property.type",
        string="Property Type",
        related="property_id.property_type_id",
        store=True,
    )

    create_date = fields.Datetime(
        "Created Date", default=fields.Datetime.now, readonly=True
    )
    validity_date = fields.Date(
        string="Validity Date",
        default=lambda self: fields.Date.context_today(self) + timedelta(days=7),
    )
    validity_duration = fields.Integer(
        string="Validity Duration (days)",
        compute="_compute_validity_duration",
        store=True,
    )

    @api.depends("create_date", "validity_date")
    def _compute_validity_duration(self):
        for offer in self:
            if offer.validity_date and offer.create_date:
                days_difference = (offer.validity_date - offer.create_date.date()).days
                offer.validity_duration = days_difference
            else:
                offer.validity_duration = 0

    @api.constrains("amount")
    def _check_amount(self):
        for offer in self:
            if offer.amount <= 0:
                raise ValidationError("The offer amount must be strictly positive.")

    def action_accept(self):
        for offer in self:
            if offer.status == "refused":
                raise UserError(
                    "You cannot accept an offer that has already been refused."
                )
            offer.status = "accepted"

    def action_refuse(self):
        for offer in self:
            if offer.status == "accepted":
                raise UserError(
                    "You cannot refuse an offer that has already been accepted."
                )
            offer.status = "refused"

    @api.model_create_multi
    def create(self, vals_list):
        # Process each dictionary in vals_list for multiple record creation
        for vals in vals_list:
            property_id = vals.get("property_id")
            offer_amount = vals.get("amount")

            # Retrieve the property record based on property_id
            property_record = self.env["estate.property"].browse(property_id)

            # Check if the offer amount is higher than any existing offer for the property
            if property_record.offers and any(
                offer.amount >= offer_amount for offer in property_record.offers
            ):
                raise ValidationError(
                    "The offer amount must be higher than existing offers."
                )

            # Update property status if applicable
            if property_record.status == "available":
                property_record.status = "offer_received"

        # Call the original create method to create all records in vals_list
        return super(EstatePropertyOffer, self).create(vals_list)
