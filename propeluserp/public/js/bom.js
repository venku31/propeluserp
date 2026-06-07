frappe.ui.form.on("BOM", {
	refresh(frm) {
		// Override the cancel_all_linked_docs endpoint for BOM
		const original = frappe.call;
		frm._patched_cancel = true;
	}
});

// Patch at the frappe level
const _original_cancel_all = frappe.linked_with?.cancel_all_linked_docs;