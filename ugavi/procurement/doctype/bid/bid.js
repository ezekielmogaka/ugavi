frappe.ui.form.on('Bid', {
    refresh(frm) {
        // Submit bid button
        if (frm.doc.status === 'Draft' && !frm.doc.__unsaved) {
            frm.add_custom_button('Submit Bid', () => {
                frappe.call({
                    method: 'ugavi.procurement.doctype.bid.bid.submit_bid',
                    args: { docname: frm.doc.name },
                    callback() { frm.refresh(); },
                });
            });
        }

        // Warning if late
        if (frm.doc.status === 'Late') {
            frm.dashboard.add_indicator('Late submission — rejected', 'red');
        }

        // Show encrypted status
        if (frm.doc.encrypted_content) {
            frm.dashboard.add_indicator('Bid encrypted (sealed)', 'blue');
        }
    },
});