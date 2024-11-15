import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
class FusionComponent(models.Model):
    _name = 'fusion.component'
    _description = 'Fusion Component'

    uuid = fields.Char(string='UUID', required=True, index=True, unique=True)
    name = fields.Char(string='Name', required=True)
    creation_date = fields.Datetime(string='Creation Date', required=True)
    created_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Created By',
    )

    # Versions of this component
    version_ids = fields.One2many(
        comodel_name='fusion.component.version',
        inverse_name='fusion_component_id',
        string='Component Versions',
    )

    @api.model
    def sync_component_version(self, design_version, component_data):
        component_uuid = component_data.get('uuid')
        component = self.env['fusion.component'].search([('uuid', '=', component_uuid)], limit=1)

        if not component:
            component = self.env['fusion.component'].create({
                'uuid': component_uuid,
                'name': component_data.get('name'),
                'creation_date': component_data.get('creation_date'),
                'created_by': self.env['fusion.user'].get_or_create_user(component_data.get('created_by'))
            })

        version_number = component_data.get('version_number')
        version = self.search([
            ('fusion_component_id', '=', component.id),
            ('version_number', '=', version_number)
        ], limit=1)

        if not version:
            self.create({
                'fusion_component_id': component.id,
                'version_number': version_number,
                'revision_date': component_data.get('revision_date'),
                'modified_by': self.env['fusion.user'].get_or_create_user(component_data.get('modified_by')),
                'fusion_design_version_id': design_version.id
            })
