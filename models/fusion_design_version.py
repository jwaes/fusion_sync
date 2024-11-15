import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FusionDesignVersion(models.Model):
    _name = 'fusion.design.version'
    _description = 'Fusion Design Version'

    fusion_design_id = fields.Many2one(
        comodel_name='fusion.design',
        string='Fusion Design',
        required=True,
        ondelete='cascade',
    )
    version_number = fields.Integer(string='Version Number', required=True)
    revision_date = fields.Datetime(string='Revision Date', required=True)
    modified_by = fields.Many2one(
        comodel_name='fusion.user',
        string='Modified By',
    )

    # Components in this design version
    component_version_ids = fields.One2many(
        comodel_name='fusion.component.version',
        inverse_name='fusion_design_version_id',
        string='Component Versions',
    )
