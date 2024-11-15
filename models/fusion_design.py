import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FusionDesign(models.Model):
    _name = 'fusion.design'
    _description = 'Fusion Design Document'

    uuid = fields.Char(string='UUID', required=True, index=True, unique=True)
    name = fields.Char(string='Name', required=True)
    creation_date = fields.Datetime(string='Creation Date', required=True)
    created_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Created By',
    )

    # Versions of this design
    version_ids = fields.One2many(
        comodel_name='fusion.design.version',
        inverse_name='fusion_design_id',
        string='Design Versions',
    )


    @api.model
    def sync_design(self, design_data):
        design_uuid = design_data.get('uuid')
        if not design_uuid:
            raise ValidationError("UUID is required to sync a Fusion design.")

        # Fetch or create the design
        design = self.search([('uuid', '=', design_uuid)], limit=1)
        if not design:
            design = self.create({
                'uuid': design_uuid,
                'name': design_data.get('name'),
                'creation_date': design_data.get('creation_date'),
                'created_by': self.env['fusion.user'].get_or_create_user(design_data.get('created_by'))
            })

        # Sync the design version
        version_number = design_data.get('version_number')
        version = self.env['fusion.design.version'].search([
            ('fusion_design_id', '=', design.id),
            ('version_number', '=', version_number)
        ], limit=1)

        if not version:
            version = self.env['fusion.design.version'].create({
                'fusion_design_id': design.id,
                'version_number': version_number,
                'revision_date': design_data.get('revision_date'),
                'modified_by': self.env['fusion.user'].get_or_create_user(design_data.get('modified_by'))
            })

        # Sync components for this design version
        for component_data in design_data.get('components', []):
            self.env['fusion.component.version'].sync_component_version(version, component_data)

        return design
