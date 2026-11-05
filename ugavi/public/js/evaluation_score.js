// Evaluation Score — evaluator submits their own scoring sheet.

frappe.ui.form.on('Evaluation Score', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.status === 'Draft' && frm.doc.evaluator === frappe.session.user) {
            frm.add_custom_button(__('Submit Score'), () => {
                frm.call('submit_score').then(() => frm.reload_doc());
            }).addClass('btn-primary');
        }
    }
});
