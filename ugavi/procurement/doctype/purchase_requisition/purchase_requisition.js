// Purchase Requisition client-side logic
frappe.ui.form.on('Purchase Requisition', {
    refresh(frm) {
        // Show procurement method indicator
        if (frm.doc.procurement_method && frm.doc.docstatus === 0) {
            const method_colors = {
                'Request for Quotation (Direct)': 'green',
                'Restricted Tender': 'orange',
                'Open Tender': 'blue',
                'Single Source': 'red',
            };
            const color = method_colors[frm.doc.procurement_method] || 'gray';
            frm.dashboard.add_indicator(
                `Method: ${frm.doc.procurement_method}`,
                color
            );
        }

        // Add "Create Tender" button for approved PRs
        if (frm.doc.status === 'Approved' && !frm.doc.__unsaved) {
            frm.add_custom_button('Create Tender', () => {
                frappe.call({
                    method: 'ugavi.procurement.doctype.purchase_requisition.purchase_requisition.create_tender',
                    args: { docname: frm.doc.name },
                    callback(r) {
                        if (r.message) {
                            frappe.msgprint(`Tender ${r.message} created`);
                            frm.refresh();
                        }
                    },
                });
            });
        }
    },

    estimated_value(frm) {
        // Recalculate procurement method when value changes
        if (frm.doc.estimated_value && frm.doc.estimated_value > 0) {
            frm.trigger('determine_method');
        }
    },

    determine_method(frm) {
        frappe.call({
            method: 'ugavi.procurement.services.rules_engine.determine_procurement_method',
            args: {
                estimated_value: frm.doc.estimated_value,
                donor: frm.doc.donor,
                item_category: frm.doc.item_category,
            },
            callback(r) {
                if (r.message) {
                    frm.set_value('procurement_method', r.message.method);
                }
            },
        });
    },
});