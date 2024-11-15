# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FusionComponentVersionAssemblyLine(models.Model):
    _name = 'fusion.component.version.assembly.line'
    _description = 'Fusion Component Version Assembly Line'

    parent_component_version_id = fields.Many2one(
        comodel_name='fusion.component.version',
        string='Parent Component Version',
        required=True,
        ondelete='cascade',
    )
    child_component_version_id = fields.Many2one(
        comodel_name='fusion.component.version',
        string='Child Component Version',
        required=True,
        ondelete='cascade',
    )
    quantity = fields.Integer(string='Quantity', default=1)
    sequence = fields.Integer(string='Sequence', default=10)
