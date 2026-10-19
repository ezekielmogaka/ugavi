frappe.ui.form.on('Supplier Prequalification', {
    refresh(frm) {
        // Status badge
        const badges = {
            'Prequalified': { color: 'green', label: 'Active' },
            'Suspended': { color: 'red', label: 'Suspended' },
            'Expired': { color: 'gray', label: 'Expired' },
            'Blacklisted': { color: 'darkred', label: 'Blacklisted' },
            'Under Review': { color: 'orange', label: 'Under Review' },
        };
        const badge = badges[frm.doc.status] || { color: 'gray', label: frm.doc.status };
        frm.dashboard.add_indicator(badge.label, badge.color);

        // Expiry warning
        if (frm.doc.expiry_date && frm.doc.status === 'Prequalified') {
            const days_left = frappe.datetime.get_diff(frm.doc.expiry_date, frappe.datetime.get_today());
            if (days_left <= 30 && days_left > 0) {
                frm.dashboard.add_indicator(`Expires in ${days_left} days`, 'orange');
            }
        }
    },

    status(frm) {
        // Auto-set suspension date
        if (frm.doc.status === 'Suspended' && !frm.doc.suspension_date) {
            frm.set_value('suspension_date', frappe.datetime.get_today());
        }
    },
});