import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FusionComponent(models.Model):
    _name = 'fusion.component'
    _description = 'Fusion Component'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, id'
    _sql_constraints = [
        ('uuid_unique', 'unique(uuid)', 'UUID must be unique'),
    ]

    # Basic Information
    uuid = fields.Char(
        string='UUID',
        required=True,
        index=True,
        tracking=True,
        help="Unique identifier from Fusion 360"
    )
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Name of the component in Fusion 360"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="If unchecked, it will hide the component without deleting it."
    )

    # Timestamps and User Info
    creation_date = fields.Datetime(
        string='Creation Date',
        required=True,
        tracking=True,
        help="Date when the component was created in Fusion 360"
    )
    created_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Created By',
        tracking=True,
        help="User who created the component in Fusion 360"
    )

    # Relationships
    version_ids = fields.One2many(
        comodel_name='fusion.component.version',
        inverse_name='fusion_component_id',
        string='Component Versions',
        help="List of all versions of this component"
    )
    version_count = fields.Integer(
        string='Version Count',
        compute='_compute_version_count',
        store=True,
        help="Number of versions for this component"
    )

    # Usage Information
    used_in_design_count = fields.Integer(
        string='Used In Designs',
        compute='_compute_usage_counts',
        help="Number of designs using this component"
    )

    @api.depends('version_ids')
    def _compute_version_count(self):
        for component in self:
            component.version_count = len(component.version_ids)

    def _compute_usage_counts(self):
        for component in self:
            designs = self.env['fusion.design.version'].search_count([
                ('component_version_ids.fusion_component_id', '=', component.id)
            ])
            component.used_in_design_count = designs

    @api.model
    def sync_component_version(self, design_version, component_data):
        """Synchronize component version data from Fusion 360.
        
        Args:
            design_version: The design version record this component belongs to
            component_data (dict): Data dictionary containing component information
                Required keys:
                - uuid: Unique identifier
                - name: Component name
                - creation_date: Creation timestamp
                - created_by: Creator information
                - version_number: Version number
        Returns:
            record: The synchronized component version record
        Raises:
            ValidationError: If required data is missing
        """
        component_uuid = component_data.get('uuid')
        if not component_uuid:
            raise ValidationError(_("UUID is required to sync a component."))

        # Fetch or create the component
        component = self.search([('uuid', '=', component_uuid)], limit=1)
        vals = {
            'uuid': component_uuid,
            'name': component_data.get('name'),
            'creation_date': component_data.get('creation_date'),
            'created_by': self.env['fusion.user'].get_or_create_user(component_data.get('created_by'))
        }

        if component:
            component.write(vals)
        else:
            component = self.create(vals)

        # Create or update version
        version_number = component_data.get('version_number')
        version = self.env['fusion.component.version'].search([
            ('fusion_component_id', '=', component.id),
            ('version_number', '=', version_number)
        ], limit=1)

        if not version:
            self.env['fusion.component.version'].create({
                'fusion_component_id': component.id,
                'version_number': version_number,
                'revision_date': component_data.get('revision_date'),
                'modified_by': self.env['fusion.user'].get_or_create_user(component_data.get('modified_by')),
                'fusion_design_version_id': design_version.id
            })

        return component

    def name_get(self):
        """Override name_get to include version count."""
        result = []
        for component in self:
            name = f"{component.name} ({component.version_count} versions)"
            result.append((component.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enable search by UUID or name."""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('uuid', operator, name)]
        return self._search(domain + args, limit=limit)
