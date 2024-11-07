from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FusionUser(models.Model):
    _name = 'fusion.user'
    _description = 'Fusion User'

    _sql_constraints = [
        ('uuid_uniq', 'unique(uuid)', 'UUID must be unique!'),
    ]

    uuid = fields.Char(string='UUID', required=True, index=True)
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
