import frappe


SCRIPT = """
frappe.ui.form.on("Job Card", {
    refresh(frm) {
        frm.set_query("custom_mould", function() {
            return {
                filters: {
                    item_group: "MOULD",
                    has_variants: 1
                }
            };
        });
    }
});
"""


def execute():
	if frappe.db.exists("Client Script", "JobCard"):
		frappe.db.set_value("Client Script", "JobCard", "script", SCRIPT)

	frappe.clear_cache(doctype="Job Card")
