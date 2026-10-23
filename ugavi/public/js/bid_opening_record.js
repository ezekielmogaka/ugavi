// Bid Opening Record — 3-officer sealed-bid opening UI
// Ugavi SCM v0.1.0 | [verified: Frappe 16.52.0 doctype_js hook]

frappe.ui.form.on('Bid Opening Record', {
    refresh(frm) {
        if (frm.doc.outcome === 'Success') {
            frm.dashboard.add_comment(
                __('Bids opened at {0} by {1}, {2}, and {3}.',
                    [frm.doc.opening_date, frm.doc.officer_1, frm.doc.officer_2, frm.doc.officer_3]),
                'green'
            );
        }

        // Print BOR
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print BOR'), () => {
                frappe.set_route('print', 'Bid Opening Record', frm.doc.name);
            });
        }
    },

    validate(frm) {
        if (!frm.doc.bids_opened || frm.doc.bids_opened.length === 0) {
            frappe.msgprint(__('No bids were opened.'));
            frappe.validated = false;
        }
    }
});