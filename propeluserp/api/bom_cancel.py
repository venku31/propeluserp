import frappe
import json


@frappe.whitelist()
def cancel_all_linked_docs(docs, ignore_doctypes_on_cancel_all=""):
	try:
		docs = json.loads(docs) if isinstance(docs, str) else docs

		allow = frappe.get_cached_value(
			"Propelus Settings", "Propelus Settings", "allow_cancel_and_delete_linked_bom"
		)

		if not allow:
			from frappe.desk.form.linked_with import cancel_all_linked_docs as frappe_cancel_all
			return frappe_cancel_all(
				docs=frappe.as_json(docs),
				ignore_doctypes_on_cancel_all=ignore_doctypes_on_cancel_all,
			)

		for doc_info in docs:
			doctype = doc_info.get("doctype")
			name = doc_info.get("name")
			if not doctype or not name:
				continue

			_clear_bom_reference_fields(doctype, name)

		frappe.db.commit()
		return "ok"

	except Exception as e:
		frappe.log_error(f"BOM CANCEL OVERRIDE EXCEPTION: {str(e)}\n{frappe.get_traceback()}")
		raise


def _clear_bom_reference_fields(doctype, name):
	meta = frappe.get_meta(doctype)
	bom_fields = [
		field.fieldname
		for field in meta.fields
		if field.fieldtype == "Link" and field.options == "BOM"
	]

	# also clear common BOM reference fields if present
	bom_fields.extend([f for f in ["bom", "bom_no", "production_bom"] if meta.has_field(f)])

	for fieldname in set(bom_fields):
		frappe.db.set_value(doctype, name, fieldname, "", update_modified=False)
