// Purchase Requisition — client-side form logic
// Ugavi SCM v0.1.0 | [verified: Frappe 16.52.0 doctype_js hook]

frappe.ui.form.on('Purchase Requisition', {
    refresh(frm) {
        // Show procurement method determination info
        if (frm.doc.estimated_value > 0 && frm.doc.procurement_method) {
            frm.set_df_property('procurement_method', 'description',
                `Determined by: ${frm.doc.procurement_method} at estimated value KES ${frm.doc.estimated_value.toLocaleString()}`);
        }

        // Show waiver requirement notice
        if (frm.doc.waiver_required) {
            frm.set_intro(
                __('⚠️ Threshold bypass detected. An approved Waiver is required for this procurement method.'),
                'orange'
            );
        }

        // Add custom buttons based on status
        if (frm.doc.docstatus === 0 && frm.doc.status === 'Draft') {
            frm.add_custom_button(__('Submit for Approval'), () => {
                frm.call('submit_for_approval').then(() => frm.reload_doc());
            }).addClass('btn-primary');
        }
        if (frm.doc.status === 'Pending Approval') {
            frm.add_custom_button(__('Approve'), () => {
                frappe.prompt(
                    [{ label: __('Remarks'), fieldname: 'remarks', fieldtype: 'Small Text' }],
                    (values) => frm.call('approve', values).then(() => frm.reload_doc()),
                    __('Approve Requisition'),
                    __('Approve')
                );
            }).addClass('btn-success');
            frm.add_custom_button(__('Reject'), () => {
                frappe.prompt(
                    [{ label: __('Reason'), fieldname: 'remarks', fieldtype: 'Small Text', reqd: 1 }],
                    (values) => frm.call('reject', values).then(() => frm.reload_doc()),
                    __('Reject Requisition'),
                    __('Reject')
                );
            });
        }
    },

    validate(frm) {
        // Client-side validation for common issues
        if (!frm.doc.items || frm.doc.items.length === 0) {
            frappe.msgprint(__('Please add at least one item to the requisition.'));
            frappe.validated = false;
        }
    },

    estimated_value(frm) {
        // Warn on high-value PRs
        if (frm.doc.estimated_value >= 500000) {
            frappe.show_alert({
                message: __('High-value requisition: Open Tender required per procurement rules.'),
                indicator: 'orange'
            }, 10);
        }
    },

    waiver_reference(frm) {
        if (frm.doc.waiver_reference) {
            frappe.show_alert({
                message: __('Waiver applied — procurement method manually specified.'),
                indicator: 'blue'
            });
        }
    }
});

// Item table events
frappe.ui.form.on('PR Item', {
    quantity(frm, cdt, cdn) {
        calculate_item_total(frm, cdt, cdn);
    },
    estimated_unit_price(frm, cdt, cdn) {
        calculate_item_total(frm, cdt, cdn);
    },
    items_add(frm, cdt, cdn) {
        // Nothing special on add
    }
});

function calculate_item_total(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    if (row.quantity && row.estimated_unit_price) {
        frappe.model.set_value(cdt, cdn, 'estimated_total',
            row.quantity * row.estimated_unit_price);
    }
}