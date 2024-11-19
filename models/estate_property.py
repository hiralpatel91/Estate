import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "id desc"

    # Fields
    name = fields.Char(required=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    description = fields.Text()
    postcode = fields.Char()
    image12 = fields.Binary(string="Image")
    date_availability = fields.Date()
    expected_price = fields.Float(required=True)
    selling_price = fields.Float()
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer(help="In square meters")
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        [("north", "North"), ("south", "South"), ("east", "East"), ("west", "West")],
        string="Garden Orientation",
    )
    active = fields.Boolean(default=True)
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer_id = fields.Many2one(
        "res.partner", string="Buyer Name", compute="_compute_buyer_id", store=True
    )
    seller_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda self: self.env.user
    )
    tags_ids = fields.Many2many("estate.property.tag", string="Tags")
    offers = fields.One2many("estate.property.offer", "property_id", string="Offers")
    status = fields.Selection(
        [
            ("available", "Available"),
            ("offer_received", "Offer Received"),
            ("sold", "Sold"),
            ("canceled", "Canceled"),
        ],
        default="available",
        required=True,
        copy=False,
        string="Status",
    )

    # Computed Fields
    total_area = fields.Float(compute="_compute_total_area", string="Total Area")
    best_offer = fields.Float(compute="_compute_best_offer", string="Best Offer")

    # Compute Total Area
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for property in self:
            property.total_area = property.living_area + property.garden_area

    # Compute Best Offer
    @api.depends("offers.amount")
    def _compute_best_offer(self):
        for property in self:
            property.best_offer = max(property.offers.mapped("amount"), default=0)

    # Compute Buyer ID
    @api.depends("offers")
    def _compute_buyer_id(self):
        for property in self:
            if property.offers:
                property.buyer_id = property.offers[
                    0
                ].partner_id  # Assuming the first offer is selected
            else:
                property.buyer_id = False

    # Action to cancel property
    def action_cancel(self):
        for property in self:
            if property.status == "sold":
                raise UserError("Sold properties cannot be canceled.")
            property.status = "canceled"

    # Check expected price validity
    @api.constrains("expected_price")
    def _check_expected_price(self):
        for property in self:
            if property.expected_price <= 0:
                raise ValidationError("The expected price must be strictly positive.")

    # Check selling price validity
    @api.constrains("selling_price")
    def _check_selling_price(self):
        for property in self:
            if property.selling_price < 0:
                raise ValidationError("The selling price must be positive.")

    # SQL constraint for unique property name
    _sql_constraints = [
        ("unique_property_name", "unique(name)", "The property name must be unique.")
    ]

    # Create Invoice Method
    def _create_invoice(self, partner_id, amount):
        """Create a customer invoice for the property sale."""
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)

        if not journal:
            raise UserError("Please configure your sales journal.")

        invoice_vals = {
            "partner_id": partner_id.id,
            "move_type": "out_invoice",
            "journal_id": journal.id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": f"Property Sale - {self.name}",
                        "quantity": 1.0,
                        "price_unit": amount,
                    },
                )
            ],
        }

        invoice = self.env["account.move"].create(invoice_vals)
        return invoice

    # Action to mark property as sold and create invoice
    def action_sold(self):
        # Check if an offer is accepted
        accepted_offer = self.offers.filtered(lambda o: o.status == "accepted")
        if not accepted_offer:
            raise UserError(
                "No accepted offer found. Please accept an offer before marking the property as sold."
            )

        # Create an invoice
        invoice_vals = {
            "partner_id": accepted_offer.partner_id.id,
            "move_type": "out_invoice",  # 'out_invoice' is for customer invoices
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": self.name,
                        "quantity": 1,
                        "price_unit": accepted_offer.amount,
                        "account_id": self.env["account.account"]
                        .search([("account_type", "=", "income")], limit=1)
                        .id,
                    },
                )
            ],
        }
        invoice = self.env["account.move"].create(invoice_vals)

        # Set the invoice on the property and update status to 'sold'
        self.invoice_id = invoice.id
        self.status = "sold"

    # Override write method to add validation for fields
    def write(self, vals):
        # Ensure invoice_id and buyer_id are valid before writing
        if "invoice_id" in vals:
            invoice_id = vals["invoice_id"]
            if invoice_id and not self.env["account.move"].browse(invoice_id).exists():
                raise UserError("Invalid Invoice ID.")

        if "buyer_id" in vals:
            buyer_id = vals["buyer_id"]
            if buyer_id and not self.env["res.partner"].browse(buyer_id).exists():
                raise UserError("Invalid Buyer ID.")

        # Proceed with the write operation
        return super(EstateProperty, self).write(vals)

    # Override create method to add validation for fields
    @api.model
    def create(self, vals):
        # Ensure invoice_id and buyer_id are valid before creating
        if "invoice_id" in vals:
            invoice_id = vals["invoice_id"]
            if invoice_id and not self.env["account.move"].browse(invoice_id).exists():
                raise UserError("Invalid Invoice ID.")

        if "buyer_id" in vals:
            buyer_id = vals["buyer_id"]
            if buyer_id and not self.env["res.partner"].browse(buyer_id).exists():
                raise UserError("Invalid Buyer ID.")

        # Proceed with the create operation
        return super(EstateProperty, self).create(vals)
