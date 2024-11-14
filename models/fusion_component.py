from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class FusionComponent(models.Model):
    _name = 'fusion.component'
    _description = 'Fusion Component Base'
    _sequence_field = 'code'
    _sequence_code = 'fusion.component.seq'

    _sql_constraints = [
        ('uuid_uniq', 'unique(uuid)', 'UUID must be unique!'),
    ]

    uuid = fields.Char(string='UUID', required=True, index=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, default=lambda self: self.env['ir.sequence'].next_by_code(self._sequence_code))
    creation_date = fields.Datetime(string='Creation Date', required=True)
    created_by = fields.Many2one(comodel_name='fusion.user', string='Created By')
    
    version_ids = fields.One2many(
        comodel_name='fusion.component.version',
        inverse_name='fusion_component_id',
        string='Versions',
    )

@api.model
def sync_component(self, component_data):
    component_uuid = component_data.get("uuid")
    if not component_uuid:
        raise ValidationError("UUID is required to sync a Fusion component.")

    component_name = component_data.get("name")
    creation_date = component_data.get("creation_date")

    # Access user details from the nested 'created_by' dictionary
    created_by_data = component_data.get("created_by", {})
    fusion_user_uuid = created_by_data.get("uuid")
    fusion_user_email = created_by_data.get("email")

    if not fusion_user_uuid or not fusion_user_email:
        raise ValidationError("Both UUID and email are required to sync the Fusion user.")

    # Search for or create the Fusion user
    fusion_user = self.env['fusion.user'].search([('uuid', '=', fusion_user_uuid)], limit=1)
    if not fusion_user:
        fusion_user = self.env['fusion.user'].create({
            'uuid': fusion_user_uuid,
            'email': fusion_user_email
        })

    # Define values for a new component
    vals = {
        'uuid': component_uuid,
        'name': component_name,
        'creation_date': creation_date,
        'created_by': fusion_user.id,
    }

    # Check if the component already exists by UUID
    component = self.search([('uuid', '=', component_uuid)], limit=1)
    if component:
        return component  # Return existing component without modifying immutable fields

    # If the component doesn't exist, create it with the provided values
    return self.create(vals)

