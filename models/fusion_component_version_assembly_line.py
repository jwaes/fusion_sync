# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class FusionComponentVersionAssemblyLine(models.Model):
    _name = 'fusion.component.version.assembly.line'
    _description = 'Fusion Component Version Assembly Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _rec_name = 'display_name'

    fusion_component_version_id = fields.Many2one(
        comodel_name='fusion.component.version',
        string='Component Version',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
        help="Parent component version containing this assembly line"
    )
    child_component_version_id = fields.Many2one(
        comodel_name='fusion.component.version',
        string='Child Component Version',
        required=True,
        tracking=True,
        index=True,
        help="Child component version used in this assembly"
    )
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=1,
        tracking=True,
        help="Number of instances of this component in the assembly"
    )
    sequence = fields.Integer(string='Sequence', default=10, help="Sequence order in the assembly list")
    child_component_name = fields.Char(
        string='Component Name', related='child_component_version_id.fusion_component_id.name', store=True, help="Name of the child component"
    )
    child_version_number = fields.Integer(
        string='Version', related='child_component_version_id.version_number', store=True, help="Version number of the child component"
    )
    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name', store=True, help="Combination of component name, version and quantity"
    )

    @api.depends('child_component_name', 'child_version_number', 'quantity')
    def _compute_display_name(self):
        for line in self:
            line.display_name = f"{line.child_component_name} (v{line.child_version_number}) x{line.quantity}"

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity < 1:
                raise ValidationError(_("Quantity must be greater than zero."))

    @api.constrains('fusion_component_version_id', 'child_component_version_id')
    def _check_recursive_assembly(self):
        for line in self:
            if line.fusion_component_version_id == line.child_component_version_id:
                raise ValidationError(_("A component cannot reference itself in its assembly."))
            if self._has_recursive_reference(line.fusion_component_version_id, line.child_component_version_id):
                raise ValidationError(_("Recursive assembly reference detected."))

    def _has_recursive_reference(self, parent_version, child_version):
        child_assemblies = self.search([('fusion_component_version_id', '=', child_version.id)])
        for assembly in child_assemblies:
            if assembly.child_component_version_id == parent_version:
                return True
            if self._has_recursive_reference(parent_version, assembly.child_component_version_id):
                return True
        return False

    @api.model
    def sync_assembly_line(self, assembly_line_data, component_version_id):
        child_component_uuid = assembly_line_data.get('child_component_version_id')
        child_component_version = self.env['fusion.component.version'].search([('uuid', '=', child_component_uuid)], limit=1)
        if not child_component_version:
            raise ValidationError(_("Child component version not found."))

        assembly_line = self.search([
            ('fusion_component_version_id', '=', component_version_id),
            ('child_component_version_id', '=', child_component_version.id)
        ], limit=1)

        vals = {
            'fusion_component_version_id': component_version_id,
            'child_component_version_id': child_component_version.id,
            'quantity': assembly_line_data.get('quantity', 1),
            'sequence': assembly_line_data.get('sequence', 10)
        }

        if assembly_line:
            assembly_line.write(vals)
        else:
            assembly_line = self.create(vals)
        return assembly_line


    def name_get(self):
        return [(line.id, line.display_name) for line in self]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            if name.isdigit():
                domain = ['|', ('quantity', '=', int(name)), ('child_version_number', '=', int(name))]
            else:
                domain = [('child_component_name', operator, name)]
        return self._search(domain + args, limit=limit)
