"""SMS provider adapter used by bid-opening OTP delivery."""

import frappe
from frappe import _


def send_message(user: str, message: str):
    mobile = frappe.db.get_value("User", user, "mobile_no")
    if frappe.conf.developer_mode or frappe.conf.get("ugavi_sms_stub"):
        frappe.sendmail(
            recipients=[user],
            subject="SMS Stub",
            message=f"[SMS to {mobile or 'demo handset'}] {message}",
        )
        return
    if not mobile:
        frappe.throw(_("User {0} does not have a mobile number").format(user))

    from frappe.core.doctype.sms_settings.sms_settings import send_sms

    send_sms(receiver_list=[mobile], msg=message)
