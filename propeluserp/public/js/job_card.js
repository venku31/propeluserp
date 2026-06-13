frappe.ui.form.on("Job Card", {
	setup(frm) {
		set_painting_toy_name_filter(frm);
	},

	refresh(frm) {
		set_painting_toy_name_filter(frm);
		schedule_moulding_material_fetch(frm);
		fetch_painting_details_from_part_numbers(frm);
	},

	custom_mould(frm) {
		schedule_moulding_material_fetch(frm);
		schedule_painting_details_fetch(frm, true);
	},

	production_item(frm) {
		fetch_painting_details_from_part_numbers(frm, true);
	},

	operation(frm) {
		set_painting_toy_name_filter(frm);
		fetch_painting_details_from_part_numbers(frm);
	},
});

frappe.ui.form.on("Moulding Machine Details", {
	part_number(frm, cdt, cdn) {
		fetch_moulding_materials_from_item(frm, cdt, cdn);
		set_painting_toy_name_filter(frm);
		fetch_painting_details_from_part_numbers(frm, true);
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

function schedule_painting_details_fetch(frm, force = false) {
	setTimeout(() => fetch_painting_details_from_part_numbers(frm, force), 150);
	setTimeout(() => fetch_painting_details_from_part_numbers(frm, force), 900);
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
		set_child_value_if_changed(cdt, cdn, "mould_no", "");
		set_child_value_if_changed(cdt, cdn, "no_of_cavity", "");
		set_child_value_if_changed(cdt, cdn, "rm_primary", "");
		set_child_value_if_changed(cdt, cdn, "rm_secondary", "");
		set_child_value_if_changed(cdt, cdn, "mb_primary", "");
		set_child_value_if_changed(cdt, cdn, "mb_secondary", "");
		return;
	}

	return frappe.db
		.get_doc("Item", row.part_number)
		.then((item) => {
			const cavity_attribute = (item.attributes || []).find(
				(attribute) => attribute.attribute === "Cavity",
			);

			set_child_value_if_changed(cdt, cdn, "mould_no", item.variant_of || "");
			set_child_value_if_changed(
				cdt,
				cdn,
				"no_of_cavity",
				cavity_attribute ? cavity_attribute.attribute_value : "",
			);
			set_child_value_if_changed(
				cdt,
				cdn,
				"rm_primary",
				item.custom_moulding_rm_primary || "",
			);
			set_child_value_if_changed(
				cdt,
				cdn,
				"rm_secondary",
				item.custom_moulding_rm_secondary || "",
			);
			set_child_value_if_changed(
				cdt,
				cdn,
				"mb_primary",
				item.custom_moulding_mb_primary || "",
			);
			set_child_value_if_changed(
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

	const pcs_per_hour_exact = cycle_time ? (60 / cycle_time) * cavity * 60 : 0;
	const pcs_per_hour = Math.round(pcs_per_hour_exact);
	const customer_order_quantity = Math.round(pcs_per_hour_exact * 8);
	const efficency = customer_order_quantity
		? Math.round((achived_quantity / customer_order_quantity) * 100)
		: 0;
	const raw_material_consuption_in_kgs = (runner_weight * achived_quantity) / 1000;

	set_child_value_if_changed(cdt, cdn, "pcs_per_hour", pcs_per_hour);
	set_child_value_if_changed(cdt, cdn, "customer_order_quantity", customer_order_quantity);
	set_child_value_if_changed(cdt, cdn, "efficency", efficency);
	set_child_value_if_changed(
		cdt,
		cdn,
		"raw_material_consuption_in_kgs",
		raw_material_consuption_in_kgs,
	);
}

function set_child_value_if_changed(cdt, cdn, fieldname, value) {
	const row = locals[cdt] && locals[cdt][cdn];

	if (!row) {
		return;
	}

	const current_value = row[fieldname];
	const both_numeric =
		current_value !== null &&
		current_value !== undefined &&
		current_value !== "" &&
		value !== null &&
		value !== undefined &&
		value !== "" &&
		!Number.isNaN(Number(current_value)) &&
		!Number.isNaN(Number(value));

	if (both_numeric && Math.abs(flt(current_value) - flt(value)) < 0.000001) {
		return;
	}

	if (!both_numeric && String(current_value || "") === String(value || "")) {
		return;
	}

	frappe.model.set_value(cdt, cdn, fieldname, value);
}

function get_moulding_part_numbers(frm) {
	return [
		...new Set(
			(frm.doc.custom_moulding_machine_details || [])
				.map((row) => row.part_number)
				.filter(Boolean),
		),
	];
}

function set_painting_toy_name_filter(frm) {
	if (!frm.fields_dict || !frm.fields_dict.custom_painting_det) {
		return;
	}

	frm.set_query("toy_name", "custom_painting_det", () => {
		return {
			query: "propeluserp.api.job_card.get_moulding_part_number_query",
			filters: {
				work_order: frm.doc.work_order,
				job_card: frm.doc.name,
			},
		};
	});
}

function fetch_painting_details_from_part_numbers(frm, force = false) {
	if (!frm.fields_dict || !frm.fields_dict.custom_painting_det) {
		return;
	}

	if (frm.doc.operation !== "Painting") {
		return;
	}

	if (!force && (frm.doc.custom_painting_det || []).length) {
		return;
	}

	frappe
		.call({
			method: "propeluserp.api.job_card.get_painting_details_from_moulding_job_cards",
			args: {
				work_order: frm.doc.work_order,
				job_card: frm.doc.name,
			},
		})
		.then((response) => {
			const painting_rows = response.message || [];

			if (!painting_rows.length) {
				if (force) {
					frm.clear_table("custom_painting_det");
					frm.refresh_field("custom_painting_det");
				}
				return;
			}

			frm.clear_table("custom_painting_det");

			painting_rows.forEach((source_row) => {
				const target_row = frm.add_child("custom_painting_det");
				target_row.toy_name = source_row.toy_name;
				target_row.description = source_row.description;
				target_row.paint_1 = source_row.paint_1;
				target_row.paint_2 = source_row.paint_2;
				target_row.paint_3 = source_row.paint_3;
				target_row.paint_4 = source_row.paint_4;
			});

			frm.refresh_field("custom_painting_det");
		});
}
