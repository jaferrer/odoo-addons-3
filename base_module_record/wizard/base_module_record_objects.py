# See LICENSE file for full copyright and licensing details.

from . import base_module_save
from odoo.tools import ustr
from odoo.tools.translate import _
from odoo import models, fields, api


class BaseModuleRecord(models.TransientModel):
    _name = 'base.module.record'
    _description = "Base Module Record"

    @api.model
    def _get_default_objects(self):
        names = ('ir.ui.view', 'ir.ui.menu', 'ir.model',
                 'ir.model.fields', 'ir.model.access',
                 'res.partner', 'res.partner.address',
                 'res.partner.category', 'workflow',
                 'workflow.activity', 'workflow.transition',
                 'ir.actions.server', 'ir.server.object.lines')
        return self.env['ir.model'].search([('model', 'in', names)])

    check_date = fields.Datetime(string='Record from Date', required=True,
                                 default=fields.Datetime.now)
    objects = fields.Many2many('ir.model', 'base_module_record_object_rel',
                               'objects',
                               'model_id', string='Objects',
                               default=_get_default_objects)
    filter_cond = fields.Selection([('created', 'Created'),
                                    ('modified', 'Modified'),
                                    ('created_modified', 'Created & Modified')
                                    ], string='Records only', required=True,
                                   default='created')

    def record_objects(self):
        data = self.read([])[0]
        check_date = data['check_date']
        filter_cond = data['filter_cond']
        mod_obj = self.env['ir.model']
        recording_data = []
        for obj_id in data['objects']:
            obj_name = (mod_obj.browse(obj_id)).model
            obj_pool = self.env[obj_name]
            if filter_cond == 'created':
                search_condition = [('create_date', '>', check_date)]
            elif filter_cond == 'modified':
                search_condition = [('write_date', '>', check_date)]
            elif filter_cond == 'created_modified':
                search_condition = ['|', ('create_date', '>', check_date),
                                    ('write_date', '>', check_date)]
            if '_log_access' in dir(obj_pool):
                if not (obj_pool._log_access):
                    search_condition = []
                if '_auto' in dir(obj_pool):
                    if not obj_pool._auto:
                        continue
            search_ids = obj_pool.search(search_condition)
            for s_id in search_ids:
                dbname = self.env.cr.dbname
                args = (dbname, self.env.user.id, obj_name, 'copy',
                        s_id.id, {})
                recording_data.append(('query', args, {}, s_id.id))
        if len(recording_data):
            res_id = self.env.ref('base_module_record.info_start_form_view').id
            self = self.with_context({'recording_data': recording_data})
            return {
                'name': _('Module Recording'),
                'context': self._context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'base.module.record.objects',
                'views': [(res_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        res_id = self.env.ref(
            'base_module_record.module_recording_message_view').id
        return {
            'name': _('Module Recording'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'base.module.record.objects',
            'views': [(res_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class BaseModuleRecordObjects(models.TransientModel):
    _name = 'base.module.record.objects'
    _description = "Base Module Record Objects"

    @api.model
    def inter_call(self, data):
        ctx = dict(self._context)
        ctx.update(({'depends': {}}))
        res = base_module_save._create_module(self.with_context(ctx), data)
        res_id = self.env.ref('base_module_record.module_create_form_view').id
        rec_id = self.create({
            'module_filename': ustr(res['module_filename']),
            'module_file': ustr(res['module_file']),
            'name': ustr(res['name']),
            'directory_name': ustr(res['directory_name']),
            'version': ustr(res['version']),
            'author': ustr(res['author']),
            'website': ustr(res['website']),
            'category': ustr(res['category']),
            'description': ustr(res['description']),
        }).id
        return {
            'name': _('Module Recording'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': rec_id,
            'res_model': 'base.module.record.objects',
            'views': [(res_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    name = fields.Char(string='Module Name', size=64)
    directory_name = fields.Char(string='Directory Name', size=32)
    version = fields.Char(string='Version', default='11.0', size=16)
    author = fields.Char(string='Author', size=64, required=True,
                         default='Odoo SA')
    category = fields.Char(string='Category', size=64, required=True,
                           default='Vertical Modules/Parametrization')
    website = fields.Char(string='Documentation URL', size=64, required=True,
                          default='https://www.odoo.com')
    description = fields.Text(string='Full Description')
    data_kind = fields.Selection([('demo', 'Demo Data'),
                                  ('update', 'Normal Data')],
                                 string='Type of Data', required=True,
                                 default='update')
    module_file = fields.Binary('Module .zip File', filename="module_filename")
    module_filename = fields.Char('Filename', size=64)
