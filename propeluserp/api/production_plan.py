import frappe


def sync_custom_supplier(doc, method=None):
	parent_supplier = doc.get("custom_supplier")

	for row in doc.get("sub_assembly_items") or []:
		if row.type_of_manufacturing != "Subcontract":
			continue

		if not row.meta.has_field("custom_supplier"):
			continue

		row.custom_supplier = row.custom_supplier or parent_supplier or row.supplier
		row.supplier = row.custom_supplier or row.supplier

		if row.qty and not row.supplier:
			frappe.throw(
				frappe._("Row #{0}: Supplier is required for Subcontract sub assembly item").format(
					row.idx
				)
			)
