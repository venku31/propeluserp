frappe.ui.form.on("Job Card", {
	refresh(frm) {
		if (frm.doc.operation === "Moulding") {
			frm.add_custom_button(__("View Mouldig Production Details"), () => {
				open_moulding_production_report(frm);
			});
		}
	},

	validate(frm) {
		validate_unique_assembly_production_rows(frm);
		if (frm.doc.operation === "Moulding" && (frm.doc.custom_moulding_machine_details || []).length) {
			update_time_logs_completed_qty_from_moulding(frm);
		}
		if (frm.doc.operation === "Assembly" && (frm.doc.custom_assembly_detail || []).length) {
			update_time_logs_completed_qty_from_assembly(frm);
		}
		if (frm.doc.operation === "Painting" && (frm.doc.custom_painting_det || []).length) {
			update_time_logs_completed_qty_from_painting(frm);
		}
	},

	before_submit(frm) {
		if (frm.doc.operation === "Moulding" && (frm.doc.custom_moulding_machine_details || []).length) {
			update_time_logs_completed_qty_from_moulding(frm);
		}
		if (frm.doc.operation === "Assembly" && (frm.doc.custom_assembly_detail || []).length) {
			update_time_logs_completed_qty_from_assembly(frm);
		}
	},

	custom_daily_moulding_details(frm) {
		show_daily_moulding_details_dialog(frm);
	},

	custom_add_daily_assembly_production(frm) {
		show_daily_assembly_production_dialog(frm);
	},

	custom_daily_painting_details(frm) {
		show_daily_painting_details_dialog(frm);
	},
});

function open_moulding_production_report(frm) {
	const filters = {
		from_date: frappe.datetime.month_start(),
		to_date: frappe.datetime.get_today(),
	};

	if (frm.doc.work_order) {
		filters.work_order = frm.doc.work_order;
	}

	if (frm.doc.sales_order) {
		filters.sales_order = frm.doc.sales_order;
		frappe.set_route("query-report", "Mouldig Production Details", filters);
		return;
	}

	if (!frm.doc.work_order) {
		frappe.set_route("query-report", "Mouldig Production Details", filters);
		return;
	}

	frappe.db.get_value("Work Order", frm.doc.work_order, "sales_order").then((response) => {
		if (response.message && response.message.sales_order) {
			filters.sales_order = response.message.sales_order;
		}

		frappe.set_route("query-report", "Mouldig Production Details", filters);
	});
}

frappe.ui.form.on("Assembly Details", {
	target(frm, cdt, cdn) {
		calculate_assembly_row(frm, cdt, cdn);
		recalculate_assembly_cumulative(frm);
	},

	achieve_qty(frm, cdt, cdn) {
		calculate_assembly_row(frm, cdt, cdn);
		recalculate_assembly_cumulative(frm);
		update_time_logs_completed_qty_from_assembly(frm);
		frm.refresh_field("time_logs");
	},

	toy_name(frm) {
		recalculate_assembly_cumulative(frm);
	},

	date(frm) {
		recalculate_assembly_cumulative(frm);
	},
});

frappe.ui.form.on("Moulding Machine Details", {
	custom_moulding_machine_details_add(frm, cdt, cdn) {
		set_child_value_if_changed(cdt, cdn, "date", frappe.datetime.get_today());
	},

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
		update_time_logs_completed_qty_from_moulding(frm);
		frm.refresh_field("time_logs");
	},
});

function fetch_moulding_materials_from_item(frm, cdt, cdn) {
	const row = locals[cdt][cdn];

	if (!row.part_number) {
		set_child_value_if_changed(cdt, cdn, "mould_no", "");
		set_child_value_if_changed(cdt, cdn, "no_of_cavity", "");
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
			set_child_value_if_empty(
				cdt,
				cdn,
				"rm_primary",
				item.custom_moulding_rm_primary || "",
			);
			set_child_value_if_empty(
				cdt,
				cdn,
				"rm_secondary",
				item.custom_moulding_rm_secondary || "",
			);
			set_child_value_if_empty(
				cdt,
				cdn,
				"mb_primary",
				item.custom_moulding_mb_primary || "",
			);
			set_child_value_if_empty(
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

function update_time_logs_completed_qty_from_moulding(frm) {
	const completed_qty = (frm.doc.custom_moulding_machine_details || []).reduce(
		(total, row) => total + flt(row.achived_quantity),
		0,
	);
	update_job_card_completed_qty(frm, completed_qty);

	if (frm.doc.sub_operations && frm.doc.sub_operations.length) {
		frm.doc.sub_operations.forEach((row) => {
			row.completed_qty = completed_qty;
		});
		frm.refresh_field("sub_operations");
	}
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

function set_child_value_if_empty(cdt, cdn, fieldname, value) {
	const row = locals[cdt] && locals[cdt][cdn];

	if (!row || row[fieldname] || !value) {
		return;
	}

	frappe.model.set_value(cdt, cdn, fieldname, value);
}

function show_daily_moulding_details_dialog(frm) {
	if (!frm.doc.custom_mould) {
		frappe.msgprint({
			title: __("Mould Required"),
			indicator: "red",
			message: __("Please select Mould before adding Daily Moulding Details."),
		});
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Daily Moulding Details"),
		fields: [
			{
				fieldname: "date",
				fieldtype: "Date",
				label: __("Date"),
				default: frappe.datetime.get_today(),
				reqd: 1,
			},
			{
				fieldname: "part_number",
				fieldtype: "Link",
				label: __("Part Number"),
				options: "Item",
				reqd: 1,
				get_query() {
					return get_moulding_part_number_query(frm);
				},
				onchange() {
					fetch_moulding_dialog_materials(frm, dialog);
				},
			},
			{
				fieldname: "machine",
				fieldtype: "Link",
				label: __("Machine"),
				options: "Machine",
				default: frm.doc.custom_machine,
			},
			{
				fieldname: "shift",
				fieldtype: "Select",
				label: __("Shift"),
				options: "\nDay\nNight",
			},
			{
				fieldname: "mould_no",
				fieldtype: "Link",
				label: __("Mould No"),
				options: "Item",
				default: frm.doc.custom_mould,
			},
			{
				fieldname: "cycle_time_sec",
				fieldtype: "Float",
				label: __("Cycle Time Sec"),
			},
			{
				fieldname: "runner_weight",
				fieldtype: "Float",
				label: __("Runner Weight"),
			},
			{
				fieldname: "no_of_cavity",
				fieldtype: "Float",
				label: __("No of Cavity"),
			},
			{
				fieldname: "achived_quantity",
				fieldtype: "Int",
				label: __("Achived Quantity"),
				reqd: 1,
			},
			{
				fieldname: "moulding_column_break",
				fieldtype: "Column Break",
			},
			{
				fieldname: "rm_primary",
				fieldtype: "Link",
				label: __("RM Primary"),
				options: "Item",
			},
			{
				fieldname: "qty_rm_primary",
				fieldtype: "Float",
				label: __("Qty RM Primary"),
			},
			{
				fieldname: "rm_secondary",
				fieldtype: "Link",
				label: __("RM Secondary"),
				options: "Item",
			},
			{
				fieldname: "qty_rm_secondary",
				fieldtype: "Float",
				label: __("Qty RM Secondary"),
			},
			{
				fieldname: "mb_primary",
				fieldtype: "Link",
				label: __("MB Primary"),
				options: "Item",
			},
			{
				fieldname: "qty_mb_primary",
				fieldtype: "Float",
				label: __("Qty MB Primary"),
			},
			{
				fieldname: "mb_secondary",
				fieldtype: "Link",
				label: __("MB Secondary"),
				options: "Item",
			},
			{
				fieldname: "qty_mb_secondary",
				fieldtype: "Float",
				label: __("Qty MB Secondary"),
			},
			{
				fieldname: "counter_reading",
				fieldtype: "Data",
				label: __("Counter Reading"),
			},
			{
				fieldname: "remarks",
				fieldtype: "Small Text",
				label: __("Remarks"),
			},
		],
		primary_action_label: __("Submit"),
		primary_action(values) {
			const row = frm.add_child("custom_moulding_machine_details");

			Object.assign(row, values);
			calculate_moulding_row(frm, row.doctype, row.name);
			update_time_logs_completed_qty_from_moulding(frm);
			frm.refresh_field("custom_moulding_machine_details");
			frm.refresh_field("time_logs");
			dialog.hide();

			const save_action = frm.doc.docstatus === 1 ? "Update" : undefined;

			frm.save(save_action).then(() => {
				frappe.show_alert({
					message: __("Daily moulding details added"),
					indicator: "green",
				});
			});
		},
	});

	dialog.show();
}

function get_moulding_part_number_query(frm) {
	return {
		filters: {
			variant_of: frm.doc.custom_mould,
			disabled: 0,
		},
	};
}

function fetch_moulding_dialog_materials(frm, dialog) {
	const part_number = dialog.get_value("part_number");

	if (!part_number) {
		return;
	}

	frappe.db.get_doc("Item", part_number).then((item) => {
		if (item.variant_of && item.variant_of !== frm.doc.custom_mould) {
			dialog.set_value("part_number", "");
			frappe.msgprint({
				title: __("Invalid Part Number"),
				indicator: "red",
				message: __("Please select a Part Number belonging to mould {0}.", [
					frm.doc.custom_mould,
				]),
			});
			return;
		}

		const cavity_attribute = (item.attributes || []).find(
			(attribute) => attribute.attribute === "Cavity",
		);

		set_dialog_value_if_empty(dialog, "mould_no", item.variant_of || frm.doc.custom_mould);
		set_dialog_value_if_empty(
			dialog,
			"no_of_cavity",
			cavity_attribute ? cavity_attribute.attribute_value : "",
		);
		set_dialog_value_if_empty(dialog, "rm_primary", item.custom_moulding_rm_primary);
		set_dialog_value_if_empty(dialog, "rm_secondary", item.custom_moulding_rm_secondary);
		set_dialog_value_if_empty(dialog, "mb_primary", item.custom_moulding_mb_primary);
		set_dialog_value_if_empty(dialog, "mb_secondary", item.custom_moulding_mb_secondary);
	});
}

function set_dialog_value_if_empty(dialog, fieldname, value) {
	if (!dialog.get_value(fieldname) && value) {
		dialog.set_value(fieldname, value);
	}
}

function show_daily_assembly_production_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Add Daily Assembly Production"),
		fields: [
			{
				fieldname: "date",
				fieldtype: "Date",
				label: __("Date"),
				default: frappe.datetime.get_today(),
				reqd: 1,
			},
			{
				fieldname: "toy_name",
				fieldtype: "Link",
				label: __("Product Name"),
				options: "Item",
				default: frm.doc.production_item,
				reqd: 1,
			},
			{
				fieldname: "manpower_used",
				fieldtype: "Float",
				label: __("Manpower Used"),
			},
			{
				fieldname: "target",
				fieldtype: "Float",
				label: __("Target"),
			},
			{
				fieldname: "achieve_qty",
				fieldtype: "Float",
				label: __("Achieve Qty"),
				reqd: 1,
			},
			{
				fieldname: "production_column_break",
				fieldtype: "Column Break",
			},
			{
				fieldname: "supervisor",
				fieldtype: "Link",
				label: __("Supervisor"),
				options: "Employee",
				reqd: 1,
			},
			{
				fieldname: "shift",
				fieldtype: "Select",
				label: __("Shift"),
				options: "\nDay\nNight",
				reqd: 1,
			},
		],
		primary_action_label: __("Submit"),
		primary_action(values) {
			if (has_duplicate_assembly_production(frm, values.date, values.toy_name)) {
				show_duplicate_assembly_message(values.date, values.toy_name);
				return;
			}

			const row = frm.add_child("custom_assembly_detail");

			Object.assign(row, values);
			calculate_assembly_row(frm, row.doctype, row.name);
			recalculate_assembly_cumulative(frm);
			update_time_logs_completed_qty_from_assembly(frm);
			frm.refresh_field("custom_assembly_detail");
			frm.refresh_field("time_logs");
			dialog.hide();

			const save_action = frm.doc.docstatus === 1 ? "Update" : undefined;

			frm.save(save_action).then(() => {
				frappe.show_alert({
					message: __("Daily assembly production added"),
					indicator: "green",
				});
			});
		},
	});

	dialog.show();
}

function calculate_assembly_row(frm, cdt, cdn) {
	const row = locals[cdt] && locals[cdt][cdn];

	if (!row) {
		return;
	}

	const target = flt(row.target);
	const achieve_qty = flt(row.achieve_qty);
	const profit_loss_qty = achieve_qty - target;

	set_child_value_if_changed(cdt, cdn, "efficiency", target ? (achieve_qty / target) * 100 : 0);
	set_child_value_if_changed(cdt, cdn, "profit_loss_qty", profit_loss_qty);
	set_child_value_if_changed(cdt, cdn, "pl_amount", profit_loss_qty);
}

function update_time_logs_completed_qty_from_assembly(frm) {
	const completed_qty = (frm.doc.custom_assembly_detail || []).reduce(
		(total, row) => total + flt(row.achieve_qty),
		0,
	);
	update_job_card_completed_qty(frm, completed_qty);

	if (frm.doc.sub_operations && frm.doc.sub_operations.length) {
		frm.doc.sub_operations.forEach((row) => {
			row.completed_qty = completed_qty;
		});
		frm.refresh_field("sub_operations");
	}
}

function recalculate_assembly_cumulative(frm) {
	const rows = frm.doc.custom_assembly_detail || [];
	const cumulative_by_product = {};

	rows.forEach((row) => {
		const product = row.toy_name || "";
		cumulative_by_product[product] = (cumulative_by_product[product] || 0) + flt(row.achieve_qty);
		set_child_value_if_changed(
			row.doctype,
			row.name,
			"achieve_qty_cumulative",
			cumulative_by_product[product],
		);
	});
}

function validate_unique_assembly_production_rows(frm) {
	const rows = frm.doc.custom_assembly_detail || [];
	const seen = {};

	rows.forEach((row) => {
		if (!row.date || !row.toy_name) {
			return;
		}

		const key = get_assembly_production_key(row.date, row.toy_name);

		if (seen[key]) {
			show_duplicate_assembly_message(row.date, row.toy_name);
			frappe.validated = false;
		}

		seen[key] = true;
	});
}

function has_duplicate_assembly_production(frm, date, product_name) {
	const key = get_assembly_production_key(date, product_name);

	return (frm.doc.custom_assembly_detail || []).some((row) => {
		return row.date && row.toy_name && get_assembly_production_key(row.date, row.toy_name) === key;
	});
}

function get_assembly_production_key(date, product_name) {
	const normalized_date =
		date instanceof Date ? frappe.datetime.obj_to_str(date) : String(date || "").trim();

	return [normalized_date, product_name].join("::");
}

function show_duplicate_assembly_message(date, product_name) {
	frappe.msgprint({
		title: __("Duplicate Entry"),
		indicator: "red",
		message: __(
			"Assembly production is already added for {0} on {1}. Please update the existing row instead.",
			[product_name, frappe.datetime.str_to_user(date)],
		),
	});
}

function show_daily_painting_details_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Daily Painting Details"),
		fields: [
			{
				fieldname: "date",
				fieldtype: "Date",
				label: __("Date"),
				default: frappe.datetime.get_today(),
				reqd: 1,
			},
			{
				fieldname: "toy_name",
				fieldtype: "Link",
				label: __("Toy Name"),
				options: "Item",
				default: frm.doc.production_item,
				reqd: 1,
			},
			{
				fieldname: "description",
				fieldtype: "Data",
				label: __("Description"),
			},
			{
				fieldname: "type",
				fieldtype: "Select",
				label: __("Type"),
				options: "\nPAD\nSPRAY",
			},
			{
				fieldname: "color_sequence",
				fieldtype: "Int",
				label: __("Color Sequence"),
			},
			{
				fieldname: "completed_qty",
				fieldtype: "Float",
				label: __("Completed Qty"),
				reqd: 1,
			},
			{
				fieldname: "paint_column_break",
				fieldtype: "Column Break",
			},
			{
				fieldname: "paint_1",
				fieldtype: "Link",
				label: __("Paint1"),
				options: "Item",
			},
			{
				fieldname: "paint_2",
				fieldtype: "Link",
				label: __("Paint2"),
				options: "Item",
			},
			{
				fieldname: "paint_3",
				fieldtype: "Link",
				label: __("Paint3"),
				options: "Item",
			},
			{
				fieldname: "paint_4",
				fieldtype: "Link",
				label: __("Paint4"),
				options: "Item",
			},
			{
				fieldname: "consumption_per_piece",
				fieldtype: "Float",
				label: __("Consumption Per Piece (Gram)"),
			},
			{
				fieldname: "remarks",
				fieldtype: "Small Text",
				label: __("Remarks"),
			},
		],
		primary_action_label: __("Submit"),
		primary_action(values) {
			const row = frm.add_child("custom_painting_det");

			Object.assign(row, values);
			update_time_logs_completed_qty_from_painting(frm);
			frm.refresh_field("custom_painting_det");
			frm.refresh_field("time_logs");
			dialog.hide();

			const save_action = frm.doc.docstatus === 1 ? "Update" : undefined;

			frm.save(save_action).then(() => {
				frappe.show_alert({
					message: __("Daily painting details added"),
					indicator: "green",
				});
			});
		},
	});

	dialog.show();
}

function update_time_logs_completed_qty_from_painting(frm) {
	const completed_qty = (frm.doc.custom_painting_det || []).reduce(
		(total, row) => total + flt(row.completed_qty),
		0,
	);
	update_job_card_completed_qty(frm, completed_qty);
}

function update_job_card_completed_qty(frm, completed_qty) {
	let time_log = (frm.doc.time_logs || [])[0];

	if (!time_log) {
		time_log = frm.add_child("time_logs");
	}

	time_log.completed_qty = completed_qty;
	frm.doc.total_completed_qty = completed_qty;
	frm.refresh_field("total_completed_qty");
}
