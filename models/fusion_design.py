import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FusionDesign(models.Model):
    _name = 'fusion.design'
    _description = 'Fusion Design Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, id'

    # Basic Information
    uuid = fields.Char(
        string='UUID',
        required=True,
        index=True,
        unique=True,
        tracking=True,
        help="Unique identifier from Fusion 360"
    )
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Name of the design in Fusion 360"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="If unchecked, it will hide the design without deleting it."
    )

    # Timestamps and User Info
    creation_date = fields.Datetime(
        string='Creation Date',
        required=True,
        tracking=True,
        help="Date when the design was created in Fusion 360"
    )
    created_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Created By',
        tracking=True,
        help="User who created the design in Fusion 360"
    )

    # Relationships
    version_ids = fields.One2many(
        comodel_name='fusion.design.version',
        inverse_name='fusion_design_id',
        string='Design Versions',
        help="List of all versions of this design"
    )
    version_count = fields.Integer(
        string='Version Count',
        compute='_compute_version_count',
        store=True,
        help="Number of versions for this design"
    )

    @api.depends('version_ids')
    def _compute_version_count(self):
        for design in self:
            design.version_count = len(design.version_ids)

    @api.model
    def sync_design(self, design_data):
        """Synchronize design data from Fusion 360.
        
        Args:
            design_data (dict): Data dictionary containing design information
                Required keys:
                - uuid: Unique identifier
                - name: Design name
                - creation_date: Creation timestamp
                - created_by: Creator information
                - version_number: Version number
                - components: List of component data
        Returns:
            record: The synchronized design record
        Raises:
            ValidationError: If required data is missing
        """
        design_uuid = design_data.get('uuid')
        if not design_uuid:
            raise ValidationError(_("UUID is required to sync a Fusion design."))

        # Fetch or create the design
        design = self.search([('uuid', '=', design_uuid)], limit=1)
        vals = {
            'uuid': design_uuid,
            'name': design_data.get('name'),
            'creation_date': design_data.get('creation_date'),
            'created_by': self.env['fusion.user'].get_or_create_user(design_data.get('created_by'))
        }

        if design:
            design.write(vals)
        else:
            design = self.create(vals)

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

    def name_get(self):
        """Override name_get to include version count."""
        result = []
        for design in self:
            name = f"{design.name} ({design.version_count} versions)"
            result.append((design.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enable search by UUID or name."""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('uuid', operator, name)]
        return self._search(domain + args, limit=limit)
