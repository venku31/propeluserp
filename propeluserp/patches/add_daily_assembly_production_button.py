import frappe


def execute():
	remove_assembly_master_field()
	add_daily_assembly_production_button()
	move_assembly_section_below_button()
	frappe.clear_cache(doctype="Job Card")


def remove_assembly_master_field():
	field_name = "Job Card-custom_assembly_master"

	if frappe.db.exists("Custom Field", field_name):
		frappe.delete_doc("Custom Field", field_name, ignore_permissions=True)


def add_daily_assembly_production_button():
	field_name = "Job Card-custom_add_daily_assembly_production"
	values = {
		"dt": "Job Card",
		"fieldname": "custom_add_daily_assembly_production",
		"label": "Add Daily Assembly Production",
		"fieldtype": "Button",
		"insert_after": "custom_assembly_details",
		"depends_on": 'eval:doc.operation=="Assembly"',
	}

	if frappe.db.exists("Custom Field", field_name):
		doc = frappe.get_doc("Custom Field", field_name)
		doc.update(values)
		doc.save(ignore_permissions=True)
		return

	doc = frappe.get_doc({"doctype": "Custom Field", **values})
	doc.insert(ignore_permissions=True)


def move_assembly_section_below_button():
	field_name = "Job Card-custom_section_break_w6xzq"

	if not frappe.db.exists("Custom Field", field_name):
		return

	doc = frappe.get_doc("Custom Field", field_name)
	doc.insert_after = "custom_add_daily_assembly_production"
	doc.save(ignore_permissions=True)
