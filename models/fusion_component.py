# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FusionComponent(models.Model):
    _name = 'fusion.component'
    _description = 'Fusion Component Base'
    _sequence_field = 'code'
    _sequence_code = 'fusion.component.seq'

    _sql_constraints = [
        ('uuid_uniq', 'unique(uuid)', 'UUID must be unique!'),
    ]


    uuid = fields.Char(string='UUID', required=True, index=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, default=lambda self: self.env['ir.sequence'].next_by_code(self._sequence_code))

    creation_date = fields.Datetime(string='Creation Date', required=True)
    created_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Created By',
    )
    # Other immutable fields...

    # One-to-many relation to component versions
    version_ids = fields.One2many(
        comodel_name='fusion.component.version',
        inverse_name='fusion_component_id',
        string='Versions',
    )
