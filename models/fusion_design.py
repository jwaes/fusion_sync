import logging
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FusionDesign(models.Model):
    _name = 'fusion.design'
    _description = 'Fusion Design Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, id'
    _sql_constraints = [
        ('uuid_unique', 'unique(uuid)', 'UUID must be unique'),
    ]

    uuid = fields.Char(string='UUID', required=True, index=True, tracking=True, help="Unique identifier from Fusion 360")
    name = fields.Char(string='Name', required=True, tracking=True, help="Name of the design in Fusion 360")
    active = fields.Boolean(string='Active', default=True, help="If unchecked, it will hide the design without deleting it.")
    creation_date = fields.Datetime(string='Creation Date', required=True, tracking=True, help="Date when the design was created in Fusion 360")
    created_by = fields.Many2one(comodel_name='fusion.user', string='Created By', tracking=True, help="User who created the design in Fusion 360")
    version_ids = fields.One2many(comodel_name='fusion.design.version', inverse_name='fusion_design_id', string='Design Versions', help="List of all versions of this design")
    version_count = fields.Integer(string='Version Count', compute='_compute_version_count', store=True, help="Number of versions for this design")

    @api.depends('version_ids')
    def _compute_version_count(self):
        for design in self:
            design.version_count = len(design.version_ids)

    @api.model
    def sync_design_structure(self, design_structure):
        design_data = design_structure.get('fusion_design')
        if not design_data:
            raise ValidationError(_("Invalid design structure: Missing fusion_design data."))

        design_uuid = design_data.get('uuid')
        if not design_uuid:
            raise ValidationError(_("UUID is required to sync a Fusion design."))

        design = self.search([('uuid', '=', design_uuid)], limit=1)
        design_vals = {
            'uuid': design_uuid,
            'name': design_data.get('name'),
            'creation_date': design_data.get('creation_date'),
            'created_by': self.env['fusion.user'].get_or_create_user(design_data.get('created_by'))
        }

        if design:
            design.write(design_vals)
        else:
            design = self.create(design_vals)

        versions_data = design_data.get('versions')
        if versions_data:
            for version_data in versions_data:
                self.env['fusion.design.version'].sync_design_version(version_data, design.id)

        return design


    def name_get(self):
        result = []
        for design in self:
            name = f"{design.name} ({design.version_count} versions)"
            result.append((design.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('uuid', operator, name)]
        return self._search(domain + args, limit=limit)
