// Bid Evaluation Summary — committee chair approval of the award recommendation.

frappe.ui.form.on('Bid Evaluation Summary', {
    refresh(frm) {
        if (frm.is_new() || !['Draft', 'Submitted'].includes(frm.doc.status)) {
            return;
        }
        const can_decide = frappe.user.has_role('Tender Committee Chair') || frappe.user.has_role('System Manager');
        if (!can_decide) {
            frm.dashboard.add_indicator(__('Awaiting Tender Committee Chair approval'), 'orange');
            return;
        }
        frm.add_custom_button(__('Approve Recommendation'), () => {
            frappe.confirm(
                __('Approve {0} at {1}? The system verifies COI declarations, approved minutes and committee scores.',
                    [frm.doc.recommended_bidder, format_currency(frm.doc.recommended_amount)]),
                () => frm.call('approve').then(() => frm.reload_doc())
            );
        }).addClass('btn-primary');
        frm.add_custom_button(__('Reject'), () => {
            frappe.prompt(
                [{ label: __('Reason'), fieldname: 'reason', fieldtype: 'Small Text', reqd: 1 }],
                (values) => frm.call('reject', values).then(() => frm.reload_doc()),
                __('Reject Recommendation'), __('Reject')
            );
        });
    }
});
