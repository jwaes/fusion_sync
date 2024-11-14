from odoo import api, fields, models, _

class FusionUser(models.Model):
    _name = 'fusion.user'
    _description = 'Fusion User'

    _sql_constraints = [
        ('uuid_uniq', 'unique(uuid)', 'UUID must be unique!'),
    ]

    uuid = fields.Char(string='UUID', required=True, index=True)
    email = fields.Char(string='Email', required=True)

    # Relation to Odoo's partner model, optional
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Related Partner',
        ondelete='set null',
    )
