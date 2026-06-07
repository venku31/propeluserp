frappe.ui.form.on("BOM", {
    before_cancel(frm) {
        frappe.validated = false;

        return new Promise((resolve) => {
            frappe.confirm(
                "On cancel, linked Material Requests, Job Cards, and Stock Entries will have their BOM reference cleared instead of being cancelled. Are you sure you want to cancel?",
                () => {
                    frappe.validated = true;
                    resolve();
                },
                () => {
                    frappe.validated = false;
                    resolve();
                }
            );
        });
    },

    refresh(frm) {
        // Patch the cancel_all_linked_docs call for BOM
        const original_cancel_linked = frappe.linked_with?.cancel_all_linked_docs?.bind(frappe.linked_with);
        if (frm.linked_with) {
            frm.linked_with.cancel_all_linked_docs = function(docs) {
                return frappe.call({
                    method: "propeluserp.api.bom_cancel.cancel_all_linked_docs",
                    args: { docs: JSON.stringify(docs) },
                    freeze: true,
                }).then(() => {
                    frm.reload_doc();
                });
            };
        }
    }
});
