# Copyright (C) 2018 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    attendance_day_ids = fields.Many2many(
        "hr.attendance.day",
        store=True,
        string="Attendances days",
        compute="_compute_att_day",
        readonly=False,
    )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.depends("date_from", "date_to", "state")
    @api.multi
    def _compute_att_day(self):
        att_days = self.env["hr.attendance.day"]
        for rd in self:
            # Remove the current leave from the attendance_day.leave_ids in
            # case of the date change
            for att in rd.attendance_day_ids:
                if self in att.leave_ids:
                    att.leave_ids = att.leave_ids.filtered(lambda r: r.id != rd.id)

            att_days = att_days.search(
                [
                    ("employee_id", "=", rd.employee_id.id),
                    ("date", ">=", rd.date_from),
                    ("date", "<=", rd.date_to),
                ]
            )

            rd.sudo().attendance_day_ids = att_days

            for att_day in att_days:
                att_day.leave_ids = att_day.leave_ids | self

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates
        given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            full_time_per_day = employee.company_id.resource_calendar_id.hours_per_day
            if not full_time_per_day:
                raise UserError(_("Working contract should define working hours per day"))

            # We get the working intervals (without the public holidays)
            attendance_interval = employee.contract_id.resource_calendar_id._attendance_intervals(date_from, date_to)

            # For each working intervals, compute the ratio over a regular day
            total = sum(
                ai.due_hours / full_time_per_day
                for start_time, end_time, ai in attendance_interval
            )

            return total

        return super()._get_number_of_days(date_from, date_to, employee_id)
