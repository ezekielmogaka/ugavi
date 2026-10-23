// Tender — client-side form logic with sealed-bid awareness
// Ugavi SCM v0.1.0 | [verified: Frappe 16.52.0 doctype_js hook]

frappe.ui.form.on('Tender', {
    refresh(frm) {
        // Status timeline indicator
        render_timeline(frm);

        // Publish action
        if (frm.doc.status === 'Draft' && !frm.is_new()) {
            frm.add_custom_button(__('Publish Tender'), () => {
                frappe.confirm(
                    __('Publish this tender? This will freeze the tender details and generate sealed-bid keys if applicable.'),
                    () => {
                        frm.call('publish').then(() => {
                            frm.reload_doc();
                            frappe.show_alert({ message: __('Tender published successfully.'), indicator: 'green' });
                        });
                    }
                );
            }).addClass('btn-primary');
        }

        // Award action
        if (frm.doc.status === 'Under Evaluation') {
            frm.add_custom_button(__('Award Tender'), () => {
                frappe.prompt([
                    { label: __('Supplier'), fieldname: 'supplier', fieldtype: 'Link', options: 'Supplier', reqd: 1 },
                    { label: __('Award Amount'), fieldname: 'amount', fieldtype: 'Currency', reqd: 1 }
                ], (values) => {
                    frm.call('award', values).then(() => {
                        frm.reload_doc();
                        frappe.show_alert({ message: __('Tender awarded. PO and contract generated.'), indicator: 'green' });
                    });
                }, __('Award Tender'), __('Award'));
            }).addClass('btn-success');
        }

        if (
            ['Published', 'Bids Received'].includes(frm.doc.status) &&
            frm.doc.submission_deadline &&
            frappe.datetime.get_diff(frappe.datetime.now_datetime(), frm.doc.submission_deadline) >= 0
        ) {
            frm.add_custom_button(__('Open Sealed Bids'), () => {
                frappe.call({
                    method: 'ugavi.procurement.services.sealed_bid.init_opening_ceremony',
                    args: { tender: frm.doc.name }
                }).then(() => {
                    frappe.prompt([
                        { label: __('Officer 1 OTP'), fieldname: 'officer_1_otp', fieldtype: 'Data', reqd: 1 },
                        { label: __('Officer 2 OTP'), fieldname: 'officer_2_otp', fieldtype: 'Data', reqd: 1 },
                        { label: __('Officer 3 OTP'), fieldname: 'officer_3_otp', fieldtype: 'Data', reqd: 1 }
                    ], (values) => {
                        frappe.call({
                            method: 'ugavi.procurement.services.sealed_bid.open_bids',
                            args: { tender: frm.doc.name, ...values }
                        }).then((opened) => {
                            frappe.set_route(
                                'Form',
                                'Bid Opening Record',
                                opened.message.opening_record
                            );
                        });
                    }, __('Enter Opening Codes'), __('Open Bids'));
                });
            }).addClass('btn-primary');
        }

        // Sealed bid key status
        if (frm.doc.public_key && frm.doc.procurement_method !== 'Request for Quotation (Direct)') {
            frm.dashboard.add_comment(
                __('🔒 Sealed bids enabled. Public key generated at {0}.', [frm.doc.key_generated_at]),
                'green'
            );
        }

        // Deadline countdown
        if (frm.doc.submission_deadline && frm.doc.status === 'Published') {
            const now = frappe.datetime.now_datetime();
            const deadline = frm.doc.submission_deadline;
            if (deadline > now) {
                const diff = frappe.datetime.get_diff(deadline, now);
                const hours = Math.floor(diff / 3600);
                frm.dashboard.add_indicator(
                    __('Bid submission closes in {0} hours.', [hours]),
                    hours > 24 ? 'green' : hours > 6 ? 'orange' : 'red'
                );
            } else {
                frm.dashboard.add_indicator(__('Submission deadline passed.'), 'red');
            }
        }
    },

    procurement_method(frm) {
        // Show sealed-bid officers when method changes
        if (frm.doc.procurement_method === 'Restricted Tender' ||
            frm.doc.procurement_method === 'Open Tender') {
            frm.toggle_display('section_crypto', true);
            frm.toggle_display('section_opening_officers', true);
        }
    },

    validate(frm) {
        // Enforce 3 distinct officers for sealed-bid tenders
        if (frm.doc.procurement_method === 'Restricted Tender' ||
            frm.doc.procurement_method === 'Open Tender') {
            const officers = [
                frm.doc.opening_officer_1,
                frm.doc.opening_officer_2,
                frm.doc.opening_officer_3
            ];
            const unique = [...new Set(officers.filter(Boolean))];
            if (unique.length !== 3) {
                frappe.msgprint(__('All three distinct Bid Opening Officers are required for sealed-bid tenders.'));
                frappe.validated = false;
            }
        }
    }
});

function render_timeline(frm) {
    const steps = [
        { status: 'Draft', label: __('Draft'), icon: 'edit' },
        { status: 'Published', label: __('Published'), icon: 'share' },
        { status: 'Bids Received', label: __('Bids Received'), icon: 'inbox' },
        { status: 'Under Evaluation', label: __('Evaluation'), icon: 'checklist' },
        { status: 'Awarded', label: __('Awarded'), icon: 'award' }
    ];
    // Render as colored pills in sidebar
    let html = '<div style="padding: 10px;">';
    for (const step of steps) {
        const active = frm.doc.status === step.status;
        const past = steps.indexOf(step) < steps.findIndex(s => s.status === frm.doc.status);
        const color = active ? '#2490ef' : past ? '#98d85b' : '#d1d8dd';
        html += `<span style="display:inline-block;padding:4px 8px;margin:2px;border-radius:12px;background:${color};color:white;font-size:11px">${step.label}</span>`;
    }
    html += '</div>';
    frm.dashboard.add_section(html);
}