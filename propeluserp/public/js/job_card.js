frappe.ui.form.on("Job Card", {
	refresh(frm) {
		schedule_moulding_material_fetch(frm);
	},

	custom_mould(frm) {
		schedule_moulding_material_fetch(frm);
	},
});

frappe.ui.form.on("Moulding Machine Details", {
	part_number(frm, cdt, cdn) {
		fetch_moulding_materials_from_item(frm, cdt, cdn);
	},

	cycle_time_sec(frm, cdt, cdn) {
		calculate_moulding_row(frm, cdt, cdn);
	},

	no_of_cavity(frm, cdt, cdn) {
		calculate_moulding_row(frm, cdt, cdn);
	},

	runner_weight(frm, cdt, cdn) {
		calculate_moulding_row(frm, cdt, cdn);
	},

	achived_quantity(frm, cdt, cdn) {
		calculate_moulding_row(frm, cdt, cdn);
	},
});

function schedule_moulding_material_fetch(frm) {
	if (!frm.doc.custom_moulding_machine_details) {
		return;
	}

	// Mould selection can populate rows asynchronously, so run once now and once after grid scripts finish.
	setTimeout(() => fetch_all_moulding_materials(frm), 100);
	setTimeout(() => fetch_all_moulding_materials(frm), 800);
}

function fetch_all_moulding_materials(frm) {
	const rows = frm.doc.custom_moulding_machine_details || [];

	rows.forEach((row) => {
		if (row.part_number) {
			fetch_moulding_materials_from_item(frm, row.doctype, row.name);
		}
	});
}

function fetch_moulding_materials_from_item(frm, cdt, cdn) {
	const row = locals[cdt][cdn];

	if (!row.part_number) {
		frappe.model.set_value(cdt, cdn, "mould_no", "");
		frappe.model.set_value(cdt, cdn, "no_of_cavity", "");
		frappe.model.set_value(cdt, cdn, "rm_primary", "");
		frappe.model.set_value(cdt, cdn, "rm_secondary", "");
		frappe.model.set_value(cdt, cdn, "mb_primary", "");
		frappe.model.set_value(cdt, cdn, "mb_secondary", "");
		return;
	}

	return frappe.db
		.get_doc("Item", row.part_number)
		.then((item) => {
			const cavity_attribute = (item.attributes || []).find(
				(attribute) => attribute.attribute === "Cavity",
			);

			frappe.model.set_value(cdt, cdn, "mould_no", item.variant_of || "");
			frappe.model.set_value(
				cdt,
				cdn,
				"no_of_cavity",
				cavity_attribute ? cavity_attribute.attribute_value : "",
			);
			frappe.model.set_value(
				cdt,
				cdn,
				"rm_primary",
				item.custom_moulding_rm_primary || "",
			);
			frappe.model.set_value(
				cdt,
				cdn,
				"rm_secondary",
				item.custom_moulding_rm_secondary || "",
			);
			frappe.model.set_value(
				cdt,
				cdn,
				"mb_primary",
				item.custom_moulding_mb_primary || "",
			);
			frappe.model.set_value(
				cdt,
				cdn,
				"mb_secondary",
				item.custom_moulding_mb_secondary || "",
			);

			calculate_moulding_row(frm, cdt, cdn);
		});
}

function calculate_moulding_row(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const cycle_time = flt(row.cycle_time_sec);
	const cavity = flt(row.no_of_cavity);
	const runner_weight = flt(row.runner_weight);
	const achived_quantity = flt(row.achived_quantity);

	const pcs_per_hour = cycle_time ? (60 / cycle_time) * cavity * 60 : 0;
	const customer_order_quantity = pcs_per_hour * 8;
	const efficency = customer_order_quantity
		? (achived_quantity / customer_order_quantity) * 100
		: 0;
	const raw_material_consuption_in_kgs = (runner_weight * achived_quantity) / 1000;

	frappe.model.set_value(cdt, cdn, "pcs_per_hour", pcs_per_hour);
	frappe.model.set_value(cdt, cdn, "customer_order_quantity", customer_order_quantity);
	frappe.model.set_value(cdt, cdn, "efficency", efficency);
	frappe.model.set_value(
		cdt,
		cdn,
		"raw_material_consuption_in_kgs",
		raw_material_consuption_in_kgs,
	);
}
