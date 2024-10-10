from odoo import api, fields, models, _, tools, Command
from odoo.exceptions import ValidationError


class CourseLesson(models.Model):
    _name = "course.lesson"
    _inherit = ['mail.thread']
    _description = "Course Lesson"
    _order = "sequence,id"

    name = fields.Char(string="Name", required=True, tracking=True)
    description = fields.Text(string="Description", required=True, tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", tracking=True)
    tag_ids = fields.Many2many('lesson.tag', 'lesson_tag_relation', 'lesson_id', 'tag_id', string="Tags")
    sequence = fields.Integer(default=10)
    is_new = fields.Boolean(string="Is New Lesson")
    description = fields.Char(string="Description")
    start_date = fields.Date(string="Start Date", required=True, tracking=True)
    created_at = fields.Datetime(string="Created At", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('created_at'):
                vals['created_at'] = fields.Datetime.now()
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _check_course_appointments(self):
        for rec in self:
            appointments = self.env['course.appointment'].search([('course_id', '=', rec.id)])
            if appointments:
                raise ValidationError(_("You cannot unlink the appointments for lesson"))


class CourseAppointment(models.Model):
    _name = "course.appointment"
    _inherit = ['mail.thread']
    _description = "Course Appointment"
    _rec_names_search = ['reference', 'course_id']
    _rec_name = 'course_id'
    _order = "sequence,id"

    reference = fields.Char(string="Reference", default='New')
    course_id = fields.Many2one("course.lesson", string="Course", tracking=True, ondelete='restrict')
    date_appointment = fields.Date(string="Date Appointment", tracking=True)
    note = fields.Text(string="Note", tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('ongoing', 'Ongoing'), ('done', 'Done'),
                              ('canceled', 'Canceled')], default='draft', tracking=True)
    sequence = fields.Integer(default=10)
    appointment_line_ids = fields.One2many('lesson.appointment.line', 'appointment_id', string="Lines")
    total_qty = fields.Float(compute='_compute_total_qty', string="Total Qty", store=True)
    start_date = fields.Date(related='course_id.start_date', store=True)

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if not vals.get('reference') or vals['reference'] == "New":
                vals['reference'] = self.env['ir.sequence'].next_by_code('course.appointment')
        return super().create(vals_list)

    @api.depends('appointment_line_ids', 'appointment_line_ids.qty')
    def _compute_total_qty(self):
        for rec in self:
            rec.total_qty = sum(rec.appointment_line_ids.mapped('qty'))

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.reference}] {rec.course_id.name}"

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_ongoing(self):
        for rec in self:
            rec.state = 'ongoing'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_canceled(self):
        for rec in self:
            rec.state = 'canceled'


class LessonTag(models.Model):
    _name = "lesson.tag"
    _description = "Lesson Tag"
    _order = "sequence,id"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=10)


class LessonAppointmentLine(models.Model):
    _name = "lesson.appointment.line"
    _description = "Lesson Appointment Line"
    _order = "sequence,id"

    sequence = fields.Integer(default=10)
    appointment_id = fields.Many2one("course.appointment", string="Appointment Line")
    product_id = fields.Many2one("product.product", string="Product Line")
    qty = fields.Float(string="Quantity")
