import frappe
from frappe import _
from frappe.utils import now_datetime


def _link_asset_movement_to_source(reference_doctype, reference_name, asset_movement_name):
    if not reference_name:
        return

    if not frappe.db.exists(reference_doctype, reference_name):
        return

    if frappe.db.get_value(reference_doctype, reference_name, "asset_movement") != asset_movement_name:
        frappe.db.set_value(reference_doctype, reference_name, "asset_movement", asset_movement_name, update_modified=False)


def _link_asset_movement_to_source(reference_doctype, reference_name, asset_movement_name, doc=None):
    try:
        frappe.db.set_value(reference_doctype, reference_name, "asset_movement", asset_movement_name, update_modified=False)
    except Exception:
        pass

    if reference_doctype == "Stock Entry" and doc:
        subcontracting_order = doc.get("subcontracting_order")
        if subcontracting_order:
            try:
                frappe.db.set_value("Subcontracting Order", subcontracting_order, "asset_movement", asset_movement_name, update_modified=False)
            except Exception:
                pass


def _create_asset_movement(reference_doctype, reference_name, asset, target_location, company, transaction_date=None, doc=None):
    exists = frappe.db.exists("Asset Movement", {"reference_doctype": reference_doctype, "reference_name": reference_name})
    if exists:
        return

    am_data = {
        "doctype": "Asset Movement",
        "company": company,
        "purpose": "Transfer",
        "transaction_date": transaction_date or now_datetime(),
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "assets": [{
            "asset": asset,
            "target_location": target_location,
        }],
    }

    if reference_doctype == "Stock Entry":
        am_data["stock_entry"] = reference_name
        if doc and doc.get("subcontracting_order"):
            am_data["subcontracting_order"] = doc.subcontracting_order

    am = frappe.get_doc(am_data)
    am.flags.ignore_mandatory = True
    am.flags.ignore_permissions = True
    am.insert(ignore_permissions=True)

    # Ensure Asset Movement is submitted
    if am.docstatus == 0:
        am.submit()

    _link_asset_movement_to_source(reference_doctype, reference_name, am.name, doc)
    frappe.msgprint(_("Created Asset Movement {0} for mould {1}").format(am.name, asset))



def on_subcontracting_order_submit(doc, method):
    """Hook: Subcontracting Order on_submit"""
    # Asset Movement is created during Stock Entry submit instead.
    return


def on_stock_entry_submit(doc, method):
    """Hook: Stock Entry on_submit"""
    if not doc.get("mould_asset") or doc.get("purpose") != "Send to Subcontractor":
        return

    # If mould_target_location is not set, derive it from Supplier.
    target_location = doc.get("mould_target_location")

    if not target_location:
        supplier = doc.get("supplier")
        if supplier:
            # Common pattern: Location name equals supplier
            if frappe.db.exists("Location", supplier):
                target_location = supplier
            else:
                # Attempt to create Location if missing.
                try:
                    loc = frappe.get_doc({
                        "doctype": "Location",
                        "location_name": supplier,
                    })
                    loc.insert(ignore_permissions=True)
                    target_location = loc.name
                except Exception:
                    target_location = None

        # Persist back to Stock Entry so it doesn't remain blank after submit.
        if target_location:
            try:
                frappe.db.set_value("Stock Entry", doc.name, "mould_target_location", target_location, update_modified=False)
            except Exception:
                pass


    if not target_location:
        frappe.msgprint(_("Please set Mould Target Location to create Asset Movement for the mould."))
        return

    _create_asset_movement(
        "Stock Entry",
        doc.name,
        doc.mould_asset,
        target_location,
        doc.company,
        doc.get("posting_date"),
        doc,
    )

