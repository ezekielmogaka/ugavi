// Supplier Prequalification — client-side form logic
// Ugavi SCM v0.1.0 | [verified: Frappe 16.52.0 doctype_js hook]

frappe.ui.form.on('Supplier Prequalification', {
    refresh(frm) {
        // Show expiry warning
        if (frm.doc.expiry_date) {
            const days_left = frappe.datetime.get_day_diff(frm.doc.expiry_date, frappe.datetime.nowdate());
            if (days_left < 0) {
                frm.set_intro(__('⚠️ This prequalification has EXPIRED. Supplier is automatically suspended.'), 'red');
            } else if (days_left <= 30) {
                frm.set_intro(__('⚠️ Pre-qualification expires in {0} days.', [days_left]), 'orange');
            }
        }

        // Renew action
        if (frm.doc.status === 'Expired' || frm.doc.status === 'Suspended') {
            frm.add_custom_button(__('Renew Pre-qualification'), () => {
                frappe.confirm(
                    __('Are you sure you want to renew this pre-qualification?'),
                    () => {
                        frappe.call({
                            method: 'ugavi.procurement.doctype.supplier_prequalification.supplier_prequalification.renew',
                            args: { prequal_name: frm.doc.name },
                            callback: (r) => {
                                if (!r.exc) frm.refresh();
                            }
                        });
                    }
                );
            }).addClass('btn-primary');
        }

        // Verify documents button
        if (frm.doc.status === 'Pending') {
            frm.add_custom_button(__('Verify Documents'), () => {
                frm.set_value('status', 'Active');
                frm.save();
            });
        }
    },

    supplier(frm) {
        if (frm.doc.supplier) {
            frappe.db.get_value('Supplier', frm.doc.supplier, 'supplier_name', (r) => {
                if (r.supplier_name) {
                    frm.set_value('supplier_name', r.supplier_name);
                }
            });
        }
    },

    validate(frm) {
        if (!frm.doc.prequalification_categories || frm.doc.prequalification_categories.length === 0) {
            frappe.msgprint(__('Please add at least one pre-qualification category.'));
            frappe.validated = false;
        }
    }
});