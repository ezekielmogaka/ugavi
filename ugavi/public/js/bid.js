// Bid — client-side form logic with encrypted bid awareness
// Ugavi SCM v0.1.0 | [verified: Frappe 16.52.0 doctype_js hook]

frappe.ui.form.on('Bid', {
    refresh(frm) {
        // Late bid indicator
        if (frm.doc.status === 'Late') {
            frm.set_intro(__('⚠️ This bid was submitted after the deadline and is marked as LATE.'), 'red');
            frm.disable_form();
        }

        // Withdrawal option
        if (frm.doc.status === 'Submitted' && !frm.doc.encrypted_content) {
            frm.add_custom_button(__('Withdraw Bid'), () => {
                frappe.confirm(
                    __('Are you sure you want to withdraw this bid?'),
                    () => {
                        frm.set_value('status', 'Withdrawn');
                        frm.save();
                    }
                );
            }).addClass('btn-danger');
        }

        // Show encrypted status
        if (frm.doc.encrypted_content) {
            frm.dashboard.add_comment(
                __('🔒 Bid content is encrypted. Decryptable only during formal 3-officer opening.'),
                'blue'
            );
        }

        // Evaluation display
        if (frm.doc.status === 'Evaluated') {
            frm.dashboard.add_indicator(
                __('Technical: {0}%, Financial: {1}%, Total: {2}%',
                    [frm.doc.technical_score, frm.doc.financial_score, frm.doc.total_score]),
                frm.doc.total_score >= 70 ? 'green' : 'orange'
            );
        }
    },

    tender(frm) {
        if (frm.doc.tender) {
            frappe.db.get_value('Tender', frm.doc.tender, ['procurement_method', 'submission_deadline', 'public_key'],
                (r) => {
                    if (r.submission_deadline) {
                        frm.set_df_property('tender', 'description',
                            __('Deadline: {0}', [frappe.datetime.str_to_user(r.submission_deadline)]));
                    }
                });
        }
    },

    validate(frm) {
        // Prevent duplicate supplier per tender
        if (frm.doc.tender && frm.doc.supplier && frm.is_new()) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Bid',
                    filters: { tender: frm.doc.tender, supplier: frm.doc.supplier },
                    fields: ['name']
                },
                callback: (r) => {
                    if (r.message && r.message.length > 0) {
                        frappe.msgprint(__('Supplier has already submitted a bid for this tender.'));
                        frappe.validated = false;
                    }
                },
                async: false
            });
        }
    }
});