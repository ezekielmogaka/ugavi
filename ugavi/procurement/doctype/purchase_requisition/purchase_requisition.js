// Purchase Requisition client-side logic
frappe.ui.form.on('Purchase Requisition', {
    refresh(frm) {
        if (frm.doc.estimated_value > 0 && frm.doc.procurement_method) {
            frm.set_df_property(
                'procurement_method',
                'description',
                `Determined by: ${frm.doc.procurement_method} at estimated value KES ${frm.doc.estimated_value.toLocaleString()}`
            );
        }

        if (frm.doc.waiver_required) {
            frm.set_intro(
                __('Threshold bypass detected. An approved Waiver is required for this procurement method.'),
                'orange'
            );
        }

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

        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.doc.status === 'Draft') {
            frm.page.set_primary_action(__('Submit for Approval'), async () => {
                if (frm.is_dirty()) {
                    await frm.save();
                }
                await frm.call('submit_for_approval');
                frm.reload_doc();
            });
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

    validate(frm) {
        if (!frm.doc.items || frm.doc.items.length === 0) {
            frappe.msgprint(__('Please add at least one item to the requisition.'));
            frappe.validated = false;
        }
    },

    waiver_reference(frm) {
        if (frm.doc.waiver_reference) {
            frappe.show_alert({
                message: __('Waiver applied — procurement method manually specified.'),
                indicator: 'blue'
            });
        }
    },
});

frappe.ui.form.on('PR Item', {
    quantity(frm, cdt, cdn) {
        calculate_item_total(cdt, cdn);
    },
    estimated_unit_price(frm, cdt, cdn) {
        calculate_item_total(cdt, cdn);
    },
});

function calculate_item_total(cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    if (row.quantity && row.estimated_unit_price) {
        frappe.model.set_value(
            cdt,
            cdn,
            'estimated_total',
            row.quantity * row.estimated_unit_price
        );
    }
}