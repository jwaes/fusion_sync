import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FusionDesignVersion(models.Model):
    _name = 'fusion.design.version'
    _description = 'Fusion Design Version'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'version_number desc, id desc'
    _rec_name = 'display_name'

    # Basic Information
    fusion_design_id = fields.Many2one(
        comodel_name='fusion.design',
        string='Fusion Design',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
        help="Reference to the parent design"
    )
    version_number = fields.Integer(
        string='Version Number',
        required=True,
        tracking=True,
        help="Version number from Fusion 360"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="If unchecked, it will hide the version without deleting it."
    )

    # Timestamps and User Info
    revision_date = fields.Datetime(
        string='Revision Date',
        required=True,
        tracking=True,
        help="Date when this version was created in Fusion 360"
    )
    modified_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Modified By',
        tracking=True,
        help="User who created this version in Fusion 360"
    )

    # Components
    component_version_ids = fields.One2many(
        comodel_name='fusion.component.version',
        inverse_name='fusion_design_version_id',
        string='Component Versions',
        help="Components used in this version of the design"
    )
    component_count = fields.Integer(
        string='Component Count',
        compute='_compute_component_count',
        store=True,
        help="Number of components in this version"
    )

    # Display Name
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Combination of design name and version number"
    )

    @api.depends('fusion_design_id.name', 'version_number')
    def _compute_display_name(self):
        for version in self:
            version.display_name = f"{version.fusion_design_id.name} (v{version.version_number})"

    @api.depends('component_version_ids')
    def _compute_component_count(self):
        for version in self:
            version.component_count = len(version.component_version_ids)

    @api.constrains('version_number')
    def _check_version_number(self):
        for version in self:
            if version.version_number < 1:
                raise ValidationError(_("Version number must be greater than zero."))
            
            # Check for duplicate version numbers within the same design
            duplicate = self.search([
                ('fusion_design_id', '=', version.fusion_design_id.id),
                ('version_number', '=', version.version_number),
                ('id', '!=', version.id)
            ], limit=1)
            
            if duplicate:
                raise ValidationError(_(
                    "Version number %(version)s already exists for design %(design)s",
                    version=version.version_number,
                    design=version.fusion_design_id.name
                ))

    def name_get(self):
        """Override name_get to show design name and version number."""
        return [(version.id, version.display_name) for version in self]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enable search by version number or design name."""
        args = args or []
        domain = []
        if name:
            if name.isdigit():
                domain = [('version_number', '=', int(name))]
            else:
                domain = [('fusion_design_id.name', operator, name)]
        return self._search(domain + args, limit=limit)
