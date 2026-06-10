import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def get_asset_current_location(asset):
    """Return current source location for an Asset.

    Used by Stock Entry mould asset grid to auto-fill `current_location`.
    """
    if not asset:
        return {"current_location": ""}

    try:
        loc = frappe.db.get_value("Asset", asset, "location")
    except Exception:
        loc = None

    return {"current_location": loc or ""}





def _link_asset_movement_to_source(reference_doctype, reference_name, asset_movement_name, doc=None):
    """Link submitted Asset Movement back to source docs.

    Important: this must only be called after the Asset Movement is submitted,
    otherwise links appear on draft/create flows.
    """
    if not reference_name:
        return

    if not frappe.db.exists(reference_doctype, reference_name):
        return

    if frappe.db.get_value(reference_doctype, reference_name, "asset_movement") != asset_movement_name:
        frappe.db.set_value(reference_doctype, reference_name, "asset_movement", asset_movement_name, update_modified=False)

    if reference_doctype == "Stock Entry" and doc:
        subcontracting_order = doc.get("subcontracting_order")
        if subcontracting_order:
            try:
                frappe.db.set_value(
                    "Subcontracting Order",
                    subcontracting_order,
                    "asset_movement",
                    asset_movement_name,
                    update_modified=False,
                )
            except Exception:
                pass



def _create_asset_movement(
    reference_doctype,
    reference_name,
    assets,
    target_locations,
    company,
    transaction_date=None,
    doc=None,
):
    # Backward compatibility: older calls may pass a single target_location string.
    if isinstance(target_locations, str):
        target_locations = {"__default__": target_locations}

    """Create (or update) Asset Movement for a Stock Entry.

    Previously this created a single-asset Asset Movement and early-returned if one
    already existed for the reference. Now it supports multiple mould assets.
    """
    if isinstance(assets, str):
        assets = [assets]

    assets = [a for a in (assets or []) if a]
    if not assets:
        return

    existing_name = frappe.db.get_value(
        "Asset Movement",
        {"reference_doctype": reference_doctype, "reference_name": reference_name},
        "name",
    )

    if existing_name:
        am = frappe.get_doc("Asset Movement", existing_name)

        # If already submitted, we can't modify directly.
        # In this integration, creation happens on first submit; if the user adds more
        # assets and re-submits after cancel/reject, it will be a new reference.
        if am.docstatus == 1:
            # Best-effort: skip.
            return

        existing_assets = {r.asset for r in (am.get("assets") or [])}
        for a in assets:
            if a in existing_assets:
                continue

            tl = target_locations.get(a)
            if not tl:
                tl = target_locations.get("__default__")

            if not tl:
                # Cannot create without target location.
                continue

            # Avoid ERPNext validation: Source and Target Location cannot be same.
            try:
                current_loc = frappe.db.get_value("Asset", a, "location")
            except Exception:
                current_loc = None

            if current_loc and str(current_loc) == str(tl):
                continue

            am.append(
                "assets",
                {
                    "asset": a,
                    "target_location": tl,
                },
            )


        am.flags.ignore_mandatory = True
        am.flags.ignore_permissions = True
        am.save(ignore_permissions=True)

    else:
        am_data = {
            "doctype": "Asset Movement",
            "company": company,
            "purpose": "Transfer",
            "transaction_date": transaction_date or now_datetime(),
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "assets": [],
        }

        # Build per-asset target location rows.
        for a in assets:
            tl = target_locations.get(a) if isinstance(target_locations, dict) else None
            if not tl and isinstance(target_locations, dict):
                tl = target_locations.get("__default__")

            if not tl:
                continue

            am_data["assets"].append({
                "asset": a,
                "target_location": tl,
            })


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

    # Only create/update Asset Movement here. Linking back to source docs
    # must happen in Stock Entry on_submit after everything is finalized.
    frappe.msgprint(_("Created/Updated Asset Movement {0} for {1} mould assets").format(am.name, len(assets)))
    return am.name






def on_subcontracting_order_submit(doc, method):
    """Hook: Subcontracting Order on_submit"""
    # Asset Movement is created during Stock Entry submit instead.
    return


def _cancel_linked_asset_movements(stock_entry_name, subcontracting_order=None):
    """Cancel Asset Movement documents linked to the given Stock Entry.

    Asset Movement can be linked to either:
    - Stock Entry (reference_doctype/reference_name)
    - Subcontracting Order (asset_movement link field)

    We cancel whichever exists to avoid link-blocking during Stock Entry cancellation.
    """
    if not stock_entry_name and not subcontracting_order:
        return

    movement_names = set()

    if stock_entry_name:
        se_movements = frappe.get_all(
            "Asset Movement",
            filters={
                "reference_doctype": "Stock Entry",
                "reference_name": stock_entry_name,
            },
            pluck="name",
        ) or []
        movement_names.update(se_movements)

    if subcontracting_order:
        sub_movements = frappe.get_all(
            "Asset Movement",
            filters={
                "subcontracting_order": subcontracting_order,
            },
            pluck="name",
        ) or []
        movement_names.update(sub_movements)

    for m in movement_names:
        try:
            mv = frappe.get_doc("Asset Movement", m)
            # Cancel only if submitted.
            if mv.docstatus == 1:
                mv.cancel()
        except Exception:
            pass



def on_stock_entry_cancel(doc, method):
    """Hook: Stock Entry on_cancel -> cancel linked Asset Movements."""
    _cancel_linked_asset_movements(doc.name)


def on_stock_entry_before_save(doc, method=None):
    """Hook: clear asset_movement for draft Stock Entries (create flow).

    Clearing here (before_save) is more reliable than validate for some
    'create from' flows.
    """
    if not doc:
        return

    # Clear only on draft/new docs. Once submitted, we let on_submit set it.
    if getattr(doc, "docstatus", 0) != 1:
        try:
            doc.set("asset_movement", "")
        except Exception:
            pass

        try:
            frappe.db.set_value("Stock Entry", doc.name, "asset_movement", "", update_modified=False)
        except Exception:
            pass


def on_stock_entry_validate(doc, method=None):
    """Hook: ensure asset_movement links are blank on draft/create flows.


    When Stock Entry is created from Subcontracting Order (before submit), we don't
    want Asset Movement links to appear yet.
    """
    if not doc:
        return

    # Only clear on new/draft; keep value once submitted.
    if getattr(doc, "docstatus", 0) != 1:
        try:
            # clear both runtime value and DB (if field exists)
            doc.set("asset_movement", "")
        except Exception:
            pass

        try:
            frappe.db.set_value("Stock Entry", doc.name, "asset_movement", "", update_modified=False)
        except Exception:
            pass





def _get_mould_assets_from_stock_entry(doc):
    """Return list of mould assets selected on Stock Entry."""
    mould_assets = []

    # New: child table (custom field/table name)
    child_rows = doc.get("custom_mould_assets") or doc.get("mould_assets") or []

    for r in child_rows:
        asset = r.get("mould_asset") if isinstance(r, dict) else getattr(r, "mould_asset", None)
        if asset:
            mould_assets.append(asset)

    # Backward compat: single field
    if not mould_assets:
        single = doc.get("mould_asset")
        if single:
            mould_assets.append(single)

    # de-dupe preserve order
    return list(dict.fromkeys(mould_assets))


def on_stock_entry_submit(doc, method):
    """Hook: Stock Entry on_submit"""
    if doc.get("purpose") != "Send to Subcontractor":
        return

    mould_assets = _get_mould_assets_from_stock_entry(doc)
    if not mould_assets:
        return

    # Prefer per-row mould_target_location if available on the child table.
    row_target_location = None
    child_rows = doc.get("custom_mould_assets") or doc.get("mould_assets") or []
    for r in child_rows:
        # r may be dict-like or ChildDoc
        if isinstance(r, dict):
            tl = r.get("mould_target_location")
        else:
            tl = getattr(r, "mould_target_location", None)
        if tl:
            row_target_location = tl
            break

    # Fallback to legacy main field mould_target_location.
    target_location = row_target_location or doc.get("mould_target_location")

    # Backward compat: if main field exists but is blank, persist derived value.
    if not doc.get("mould_target_location") and target_location:
        try:
            frappe.db.set_value(
                "Stock Entry",
                doc.name,
                "mould_target_location",
                target_location,
                update_modified=False,
            )
        except Exception:
            pass

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

    # Build per-asset target locations from child rows.
    # Supports child row field `mould_target_location`.
    target_locations = {}
    child_rows = doc.get("custom_mould_assets") or doc.get("mould_assets") or []
    for r in child_rows:
        if isinstance(r, dict):
            asset = r.get("mould_asset")
            tl = r.get("mould_target_location")
        else:
            asset = getattr(r, "mould_asset", None)
            tl = getattr(r, "mould_target_location", None)
        if asset and tl:
            target_locations[asset] = tl

    # Default fallback (derived from supplier / legacy field).
    if target_location:
        target_locations["__default__"] = target_location

    asset_movement_name = _create_asset_movement(
        "Stock Entry",
        doc.name,
        mould_assets,
        target_locations,
        doc.company,
        doc.get("posting_date"),
        doc,
    )

    # Link only after Asset Movement is submitted.
    if asset_movement_name:
        try:
            mv = frappe.get_doc("Asset Movement", asset_movement_name)
            if mv.docstatus == 1:
                _link_asset_movement_to_source("Stock Entry", doc.name, asset_movement_name, doc)
        except Exception:
            pass




