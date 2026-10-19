frappe.ui.form.on('Bid Opening Record', {
    refresh(frm) {
        // Opening status indicator
        const indicators = {
            'Success': 'green',
            'Partial': 'orange',
            'Failed': 'red',
        };
        const color = indicators[frm.doc.outcome] || 'gray';
        frm.dashboard.add_indicator(`Opening: ${frm.doc.outcome}`, color);

        // Hash verification
        if (frm.doc.record_hash) {
            frm.dashboard.add_indicator(`SHA-256: ${frm.doc.record_hash.substring(0, 16)}...`, 'blue');
        }
    },
});