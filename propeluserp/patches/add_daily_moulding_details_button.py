import frappe


def execute():
	add_daily_moulding_details_button()
	move_moulding_section_below_button()
	frappe.clear_cache(doctype="Job Card")


def add_daily_moulding_details_button():
	field_name = "Job Card-custom_daily_moulding_details"
	values = {
		"dt": "Job Card",
		"fieldname": "custom_daily_moulding_details",
		"label": "Daily Moulding Details",
		"fieldtype": "Button",
		"insert_after": "custom_machine_details",
		"depends_on": 'eval:doc.operation=="Moulding"',
	}

	if frappe.db.exists("Custom Field", field_name):
		doc = frappe.get_doc("Custom Field", field_name)
		doc.update(values)
		doc.save(ignore_permissions=True)
		return

	doc = frappe.get_doc({"doctype": "Custom Field", **values})
	doc.insert(ignore_permissions=True)


def move_moulding_section_below_button():
	field_name = "Job Card-custom_section_break_g0ufl"

	if not frappe.db.exists("Custom Field", field_name):
		return

	doc = frappe.get_doc("Custom Field", field_name)
	doc.insert_after = "custom_daily_moulding_details"
	doc.save(ignore_permissions=True)
