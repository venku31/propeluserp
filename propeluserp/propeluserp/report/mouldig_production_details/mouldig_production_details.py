import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	return get_columns(), get_data(filters)


def validate_filters(filters):
	if not filters.from_date:
		frappe.throw(_("From Date is required"))

	if not filters.to_date:
		frappe.throw(_("To Date is required"))

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be after To Date"))


def get_data(filters):
	conditions = [
		"job_card.operation = 'Moulding'",
		"job_card.docstatus < 2",
		"details.date BETWEEN %(from_date)s AND %(to_date)s",
	]

	if filters.get("work_order"):
		conditions.append("job_card.work_order = %(work_order)s")

	if filters.get("sales_order"):
		conditions.append("work_order.sales_order = %(sales_order)s")

	return frappe.db.sql(
		f"""
		SELECT
			details.date,
			job_card.name AS job_card,
			job_card.work_order,
			work_order.sales_order,
			job_card.production_item,
			job_card.custom_mould AS mould,
			details.part_number,
			details.machine,
			details.shift,
			details.mould_no,
			details.rm_primary,
			details.qty_rm_primary,
			details.rm_secondary,
			details.qty_rm_secondary,
			details.mb_primary,
			details.qty_mb_primary,
			details.mb_secondary,
			details.qty_mb_secondary,
			details.cycle_time_sec,
			details.runner_weight,
			details.no_of_cavity,
			details.pcs_per_hour,
			details.customer_order_quantity,
			details.achived_quantity,
			details.efficency,
			details.raw_material_consuption_in_kgs,
			details.counter_reading,
			details.remarks
		FROM `tabMoulding Machine Details` details
		INNER JOIN `tabJob Card` job_card
			ON details.parent = job_card.name
			AND details.parenttype = 'Job Card'
			AND details.parentfield = 'custom_moulding_machine_details'
		LEFT JOIN `tabWork Order` work_order
			ON work_order.name = job_card.work_order
		WHERE {" AND ".join(conditions)}
		ORDER BY details.date DESC, job_card.name, details.idx
		""",
		filters,
		as_dict=True,
	)


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Job Card"),
			"fieldname": "job_card",
			"fieldtype": "Link",
			"options": "Job Card",
			"width": 150,
		},
		{
			"label": _("Work Order"),
			"fieldname": "work_order",
			"fieldtype": "Link",
			"options": "Work Order",
			"width": 160,
		},
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 160,
		},
		{
			"label": _("Production Item"),
			"fieldname": "production_item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 180,
		},
		{"label": _("Mould"), "fieldname": "mould", "fieldtype": "Link", "options": "Item", "width": 120},
		{
			"label": _("Part Number"),
			"fieldname": "part_number",
			"fieldtype": "Link",
			"options": "Item",
			"width": 180,
		},
		{"label": _("Machine"), "fieldname": "machine", "fieldtype": "Link", "options": "Machine", "width": 110},
		{"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 90},
		{"label": _("Mould No"), "fieldname": "mould_no", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("RM Primary"), "fieldname": "rm_primary", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": _("Qty RM Primary"), "fieldname": "qty_rm_primary", "fieldtype": "Float", "width": 120},
		{"label": _("RM Secondary"), "fieldname": "rm_secondary", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": _("Qty RM Secondary"), "fieldname": "qty_rm_secondary", "fieldtype": "Float", "width": 130},
		{"label": _("MB Primary"), "fieldname": "mb_primary", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": _("Qty MB Primary"), "fieldname": "qty_mb_primary", "fieldtype": "Float", "width": 120},
		{"label": _("MB Secondary"), "fieldname": "mb_secondary", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": _("Qty MB Secondary"), "fieldname": "qty_mb_secondary", "fieldtype": "Float", "width": 130},
		{"label": _("Cycle Time Sec"), "fieldname": "cycle_time_sec", "fieldtype": "Float", "width": 120},
		{"label": _("Runner Weight"), "fieldname": "runner_weight", "fieldtype": "Float", "width": 120},
		{"label": _("No of Cavity"), "fieldname": "no_of_cavity", "fieldtype": "Float", "width": 110},
		{"label": _("Pcs Per Hour"), "fieldname": "pcs_per_hour", "fieldtype": "Float", "width": 110},
		{
			"label": _("Customer Order Quantity"),
			"fieldname": "customer_order_quantity",
			"fieldtype": "Int",
			"width": 160,
		},
		{"label": _("Achived Quantity"), "fieldname": "achived_quantity", "fieldtype": "Int", "width": 130},
		{"label": _("Efficency"), "fieldname": "efficency", "fieldtype": "Percent", "width": 100},
		{
			"label": _("Raw Material Consuption in Kgs"),
			"fieldname": "raw_material_consuption_in_kgs",
			"fieldtype": "Float",
			"width": 190,
		},
		{"label": _("Counter Reading"), "fieldname": "counter_reading", "fieldtype": "Data", "width": 130},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 180},
	]
