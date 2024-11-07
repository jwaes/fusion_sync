# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FusionComponentVersion(models.Model):
    _name = 'fusion.component.version'
    _description = 'Fusion Component Version'
    _order = 'fusion_component_id, version_number desc'

    fusion_component_id = fields.Many2one(
        comodel_name='fusion.component',
        string='Fusion Component',
        required=True,
        ondelete='cascade',
    )
    version_number = fields.Integer(string='Version Number', required=True)
    revision_date = fields.Datetime(string='Revision Date', required=True)
    modified_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Modified By',
    )
    # status = fields.Selection([...], string='Status')
    # Other version-specific fields...

    # One-to-many relation to assembly lines
    assembly_line_ids = fields.One2many(
        comodel_name='fusion.component.version.assembly.line',
        inverse_name='fusion_component_version_id',
        string='Assembly Lines',
    )
