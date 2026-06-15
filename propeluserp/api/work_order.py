from collections import defaultdict

import frappe


def sync_required_item_operations_from_bom(doc, method=None):
	if not doc.bom_no or not doc.get("required_items"):
		return

	operation_by_item, operation_by_item_and_row = get_bom_item_operations(doc.bom_no)

	for row in doc.required_items:
		if row.operation:
			continue

		if row.operation_row_id:
			row.operation = operation_by_item_and_row.get((row.item_code, row.operation_row_id))

		if not row.operation:
			row.operation = get_single_operation(operation_by_item.get(row.item_code))


def repair_required_item_operations(work_order):
	doc = frappe.get_doc("Work Order", work_order)
	sync_required_item_operations_from_bom(doc)
	doc.save()

	return {
		"name": doc.name,
		"updated_items": [
			{"idx": row.idx, "item_code": row.item_code, "operation": row.operation}
			for row in doc.required_items
		],
	}


def get_bom_item_operations(bom_no):
	operation_by_item = defaultdict(list)
	operation_by_item_and_row = {}

	for row in frappe.get_all(
		"BOM Item",
		filters={"parent": bom_no, "docstatus": ["<", 2]},
		fields=["item_code", "operation", "operation_row_id"],
		order_by="idx",
	):
		if not row.operation:
			continue

		operation_by_item[row.item_code].append(row.operation)

		if row.operation_row_id:
			operation_by_item_and_row[(row.item_code, row.operation_row_id)] = row.operation

	return operation_by_item, operation_by_item_and_row


def get_single_operation(operations):
	unique_operations = []

	for operation in operations or []:
		if operation not in unique_operations:
			unique_operations.append(operation)

	return unique_operations[0] if len(unique_operations) == 1 else None
