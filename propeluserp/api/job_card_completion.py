from frappe.utils import flt


def sync_completed_qty_from_custom_details(doc, method=None):
	if doc.operation == "Moulding":
		details = doc.get("custom_moulding_machine_details", [])
		completed_qty_field = "achived_quantity"
	elif doc.operation == "Assembly":
		details = doc.get("custom_assembly_detail", [])
		completed_qty_field = "achieve_qty"
	elif doc.operation == "Painting":
		details = doc.get("custom_painting_det", [])
		completed_qty_field = "completed_qty"
	else:
		return

	if not details:
		return

	completed_qty = sum(flt(row.get(completed_qty_field)) for row in details)
	sync_time_logs(doc, completed_qty)

	if doc.operation in ("Moulding", "Assembly") and doc.get("sub_operations"):
		for row in doc.sub_operations:
			row.completed_qty = completed_qty

	doc.total_completed_qty = completed_qty


def sync_time_logs(doc, completed_qty):
	if doc.get("time_logs"):
		doc.time_logs[0].completed_qty = completed_qty
		return

	doc.append("time_logs", {"completed_qty": completed_qty})
