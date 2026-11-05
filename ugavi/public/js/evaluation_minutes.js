// Evaluation Minutes — chair approval of the committee session record.

frappe.ui.form.on('Evaluation Minutes', {
    refresh(frm) {
        if (frm.is_new() || frm.doc.status !== 'Draft') {
            return;
        }
        if (!(frappe.user.has_role('Tender Committee Chair') || frappe.user.has_role('System Manager'))) {
            return;
        }
        frm.add_custom_button(__('Approve Minutes'), () => {
            frm.call('approve').then(() => frm.reload_doc());
        }).addClass('btn-primary');
        frm.add_custom_button(__('Reject'), () => {
            frappe.prompt(
                [{ label: __('Reason'), fieldname: 'reason', fieldtype: 'Small Text', reqd: 1 }],
                (values) => frm.call('reject', values).then(() => frm.reload_doc()),
                __('Reject Minutes'), __('Reject')
            );
        });
    }
});
