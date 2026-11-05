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

        if (['Under Evaluation', 'Standstill Period'].includes(frm.doc.status) && !frm.is_new()) {
            add_award_actions(frm);
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
        { status: 'Standstill Period', label: __('Standstill'), icon: 'clock' },
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

function add_award_actions(frm) {
    frm.call('get_award_recommendation').then(({ message }) => {
        const rec = (message && message.recommendation) || {};
        const standstill = (message && message.standstill) || {};

        if (frm.doc.status === 'Under Evaluation') {
            if (!rec.name) {
                frm.dashboard.add_indicator(__('Awaiting approved Bid Evaluation Summary'), 'orange');
                return;
            }
            frm.dashboard.add_indicator(
                __('Recommended: {0} ({1})', [rec.recommended_bidder, format_currency(rec.recommended_amount)]),
                'blue'
            );
            frm.add_custom_button(__('Start Standstill'), () => {
                frappe.confirm(
                    __('Notify all bidders of the intended award to {0} and open the complaint window?', [rec.recommended_bidder]),
                    () => frm.call('start_standstill').then(() => frm.reload_doc())
                );
            }).addClass('btn-primary');
            return;
        }

        if (['Active', 'Challenged'].includes(standstill.status)) {
            const ended = frappe.datetime.get_day_diff(frappe.datetime.get_today(), standstill.end_date) > 0;
            frm.dashboard.add_indicator(
                ended
                    ? __('Standstill ended {0}', [frappe.datetime.str_to_user(standstill.end_date)])
                    : __('Complaint window open until {0}', [frappe.datetime.str_to_user(standstill.end_date)]),
                standstill.status === 'Challenged' ? 'red' : 'orange'
            );
            if (ended) {
                frm.add_custom_button(__('Confirm Standstill'), () => {
                    frm.call('confirm_standstill').then(() => frm.reload_doc());
                }).addClass('btn-primary');
            }
        } else if (standstill.status === 'Resolved' && standstill.resolution === 'Award Confirmed' && rec.name) {
            frm.add_custom_button(__('Award Tender'), () => {
                frappe.confirm(
                    __('Award {0} for {1} and issue the Purchase Order?', [rec.recommended_bidder, format_currency(rec.recommended_amount)]),
                    () => frm.call('award', { supplier: rec.recommended_bidder, amount: rec.recommended_amount })
                        .then(() => frm.reload_doc())
                );
            }).addClass('btn-primary');
        }
    });
}

