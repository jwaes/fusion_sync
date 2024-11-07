from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FusionUser(models.Model):
    _name = 'fusion.user'
    _description = 'Fusion User'

    fusion_user_id = fields.Char(string='Fusion User ID', required=True, index=True)
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    role = fields.Char(string='Role')
    active = fields.Boolean(string='Active', default=True)
    creation_date = fields.Datetime(string='Creation Date', default=fields.Datetime.now)

    # Relations to Odoo models
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Related Partner',
        ondelete='set null',
    )