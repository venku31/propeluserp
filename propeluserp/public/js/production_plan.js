frappe.ui.form.on("Production Plan", {
	custom_supplier(frm) {
		frm.events.sync_custom_supplier_to_sub_assembly_items(frm);
	},

	before_save(frm) {
		frm.events.sync_custom_supplier_to_sub_assembly_items(frm);
	},

	sync_custom_supplier_to_sub_assembly_items(frm) {
		const supplier = frm.doc.custom_supplier;

		(frm.doc.sub_assembly_items || []).forEach((row) => {
			if (row.type_of_manufacturing !== "Subcontract") {
				return;
			}

			const row_supplier = row.custom_supplier || supplier;

			row.custom_supplier = row_supplier;
			row.supplier = row_supplier;

			frappe.model.set_value(row.doctype, row.name, "custom_supplier", row_supplier);
			frappe.model.set_value(row.doctype, row.name, "supplier", row_supplier);
		});

		frm.refresh_field("sub_assembly_items");
	},
});

frappe.ui.form.on("Production Plan Sub Assembly Item", {
	custom_supplier(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.supplier = row.custom_supplier;
		frappe.model.set_value(cdt, cdn, "supplier", row.custom_supplier);
	},

	type_of_manufacturing(frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (row.type_of_manufacturing === "Subcontract" && !row.custom_supplier && frm.doc.custom_supplier) {
			row.custom_supplier = frm.doc.custom_supplier;
			row.supplier = frm.doc.custom_supplier;
			frappe.model.set_value(cdt, cdn, "custom_supplier", frm.doc.custom_supplier);
			frappe.model.set_value(cdt, cdn, "supplier", frm.doc.custom_supplier);
		}
	},
});
