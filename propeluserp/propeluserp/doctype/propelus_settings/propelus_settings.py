import frappe
from frappe.model.document import Document


class PropelusSettings(Document):
	pass


def apply_ignore_links_for_bom(doc, event=None):
	if not frappe.get_single("Propelus Settings").get("allow_cancel_and_delete_linked_bom"):
		return

	if event == "before_cancel":
		doc.flags.ignore_links = True
		doc.flags.ignore_permissions = True
		return

	if event in ("after_cancel", "on_trash"):
		_clear_bom_references(doc)


def _clear_bom_references(doc):
	from frappe.model.dynamic_links import get_dynamic_link_map
	from frappe.model.rename_doc import get_link_fields

	for lf in get_link_fields(doc.doctype):
		_clear_link_field(lf["parent"], lf["fieldname"], doc.name, lf["issingle"])

	for df in get_dynamic_link_map().get(doc.doctype, []):
		_clear_dynamic_link(df.parent, df.fieldname, df.options, doc)

	frappe.db.commit()


def _clear_link_field(doctype, fieldname, value, issingle):
	if issingle:
		if frappe.db.get_single_value(doctype, fieldname) == value:
			frappe.db.set_value(doctype, doctype, fieldname, "", update_modified=False)
		return

	frappe.db.set_value(doctype, {fieldname: value}, fieldname, "", update_modified=False)


def _clear_dynamic_link(doctype, fieldname, doctype_field, doc):
	filters = {fieldname: doc.name, doctype_field: doc.doctype}
	frappe.db.set_value(doctype, filters, fieldname, "", update_modified=False)
