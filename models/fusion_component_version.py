# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class FusionComponentVersion(models.Model):
    _name = 'fusion.component.version'
    _description = 'Fusion Component Version'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'version_number desc, id desc'
    _rec_name = 'display_name'

    fusion_component_id = fields.Many2one(comodel_name='fusion.component', string='Fusion Component', required=True, ondelete='cascade', tracking=True, index=True, help="Reference to the parent component")
    version_number = fields.Integer(string='Version Number', required=True, tracking=True, help="Version number from Fusion 360")
    active = fields.Boolean(string='Active', default=True, help="If unchecked, it will hide the version without deleting it.")
    revision_date = fields.Datetime(string='Revision Date', required=True, tracking=True, help="Date when this version was created in Fusion 360")
    modified_by = fields.Many2one(comodel_name='fusion.user', string='Modified By', tracking=True, help="User who created this version in Fusion 360")
    fusion_design_version_id = fields.Many2one(comodel_name='fusion.design.version', string='Design Version', ondelete='cascade', tracking=True, help="Design version where this component is used")
    external_design_version_id = fields.Many2one(comodel_name='fusion.design.version', string='External Design Version', tracking=True, help="Reference to external design version if this component is linked to another design")
    assembly_lines = fields.One2many(comodel_name='fusion.component.version.assembly.line', inverse_name='fusion_component_version_id', string='Assembly Lines', help="List of child components in this assembly")
    assembly_line_count = fields.Integer(string='Number of Assembly Lines', compute='_compute_assembly_line_count', store=True, help="Number of child components in this assembly")
    used_in_count = fields.Integer(string='Used In', compute='_compute_used_in_count', help="Number of other components using this version")
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True, help="Combination of component name and version number")

    @api.depends('fusion_component_id.name', 'version_number')
    def _compute_display_name(self):
        for version in self:
            version.display_name = f"{version.fusion_component_id.name} (v{version.version_number})"

    @api.depends('assembly_lines')
    def _compute_assembly_line_count(self):
        for version in self:
            version.assembly_line_count = len(version.assembly_lines)

    def _compute_used_in_count(self):
        for version in self:
            used_in = self.env['fusion.component.version.assembly.line'].search_count([('child_component_version_id', '=', version.id)])
            version.used_in_count = used_in

    @api.constrains('version_number')
    def _check_version_number(self):
        for version in self:
            if version.version_number < 1:
                raise ValidationError(_("Version number must be greater than zero."))
            duplicate = self.search([
                ('fusion_component_id', '=', version.fusion_component_id.id),
                ('version_number', '=', version.version_number),
                ('id', '!=', version.id)
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "Version number %(version)s already exists for component %(component)s",
                    version=version.version_number,
                    component=version.fusion_component_id.name
                ))

    @api.model
    def sync_component_version(self, component_version_data, design_version_uuid):
        component_uuid = component_version_data.get('uuid')
        if not component_uuid:
            raise ValidationError(_("UUID is required to sync a component."))

        component = self.env['fusion.component'].search([('uuid', '=', component_uuid)], limit=1)
        if not component:
            component_data = component_version_data.copy()
            component_data['uuid'] = component_uuid
            component = self.env['fusion.component'].create(component_data)
        
        version_number_str = component_version_data.get('version_number')
        if version_number_str is not None:
            if isinstance(version_number_str, str) and version_number_str.isdigit():
                version_number = int(version_number_str)
            elif isinstance(version_number_str, int):
                version_number = version_number_str
            else:
                raise ValidationError(_("Invalid version number format."))
        else:
            version_number = 1

        version = self.search([
            ('fusion_component_id', '=', component.id),
            ('version_number', '=', version_number)
        ], limit=1)

        design_version = self.env['fusion.design.version'].search([('uuid', '=', design_version_uuid)], limit=1)
        if not design_version:
            raise ValidationError(_("Design version not found."))


        vals = {
            'fusion_component_id': component.id,
            'version_number': version_number,
            'revision_date': component_version_data.get('revision_date'),
            'modified_by': self.env['fusion.user'].get_or_create_user(component_version_data.get('modified_by')),
            'fusion_design_version_id': design_version.id
        }

        if version:
            version.write(vals)
        else:
            version = self.create(vals)

        assembly_lines_data = component_version_data.get('assembly_lines')
        if assembly_lines_data:
            for assembly_line_data in assembly_lines_data:
                self.env['fusion.component.version.assembly.line'].sync_assembly_line(
                    assembly_line_data, version.id
                )

        return version

    def name_get(self):
        return [(version.id, version.display_name) for version in self]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            if name.isdigit():
                domain = [('version_number', '=', int(name))]
            else:
                domain = [('fusion_component_id.name', operator, name)]
        return self._search(domain + args, limit=limit)
