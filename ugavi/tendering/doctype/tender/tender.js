frappe.ui.form.on('Tender', {
    refresh(frm) {
        // Publish button for draft tenders
        if (frm.doc.status === 'Draft' && !frm.doc.__unsaved) {
            frm.add_custom_button('Publish Tender', () => {
                frappe.confirm('Publish this tender? Bids will be accepted until the deadline.', () => {
                    frappe.call({
                        method: 'ugavi.tendering.doctype.tender.tender.publish',
                        args: { docname: frm.doc.name },
                        callback() { frm.refresh(); },
                    });
                });
            });
        }

        // Countdown to deadline
        if (frm.doc.submission_deadline && frm.doc.status === 'Published') {
            const now = frappe.datetime.now_datetime();
            const deadline = frm.doc.submission_deadline;
            const diff = frappe.datetime.get_diff(deadline, now);
            if (diff > 0) {
                frm.dashboard.add_indicator(`${diff} days to deadline`, 'blue');
            }
        }

        // Show officer validation result
        if (frm.doc.opening_officer_1 && frm.doc.opening_officer_2 && frm.doc.opening_officer_3) {
            const officers = [frm.doc.opening_officer_1, frm.doc.opening_officer_2, frm.doc.opening_officer_3];
            const unique = new Set(officers);
            if (unique.size === 3) {
                frm.dashboard.add_indicator('3 officers assigned', 'green');
            } else {
                frm.dashboard.add_indicator('Duplicate officers detected', 'red');
            }
        }
    },
});