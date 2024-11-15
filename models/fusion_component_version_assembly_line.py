# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class FusionComponentVersionAssemblyLine(models.Model):
    _name = 'fusion.component.version.assembly.line'
    _description = 'Fusion Component Version Assembly Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _rec_name = 'display_name'

    # Basic Information
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

    # Assembly Details
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=1,
        tracking=True,
        help="Number of instances of this component in the assembly"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Sequence order in the assembly list"
    )

    # Related Fields for Easy Access
    child_component_name = fields.Char(
        string='Component Name',
        related='child_component_version_id.fusion_component_id.name',
        store=True,
        help="Name of the child component"
    )
    child_version_number = fields.Integer(
        string='Version',
        related='child_component_version_id.version_number',
        store=True,
        help="Version number of the child component"
    )

    # Display Name
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Combination of component name, version and quantity"
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
        """Prevent recursive assembly references."""
        for line in self:
            if line.fusion_component_version_id == line.child_component_version_id:
                raise ValidationError(_("A component cannot reference itself in its assembly."))
            
            # Check for deeper recursive references
            if self._has_recursive_reference(line.fusion_component_version_id, line.child_component_version_id):
                raise ValidationError(_("Recursive assembly reference detected."))

    def _has_recursive_reference(self, parent_version, child_version):
        """Check if there's a recursive reference in the assembly structure."""
        child_assemblies = self.search([
            ('fusion_component_version_id', '=', child_version.id)
        ])
        
        for assembly in child_assemblies:
            if assembly.child_component_version_id == parent_version:
                return True
            if self._has_recursive_reference(parent_version, assembly.child_component_version_id):
                return True
        return False

    def name_get(self):
        """Override name_get to show component name, version and quantity."""
        return [(line.id, line.display_name) for line in self]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enable search by component name or version number."""
        args = args or []
        domain = []
        if name:
            if name.isdigit():
                domain = ['|',
                    ('quantity', '=', int(name)),
                    ('child_version_number', '=', int(name))
                ]
            else:
                domain = [('child_component_name', operator, name)]
        return self._search(domain + args, limit=limit)
