import frappe
from frappe import _


from frappe.utils import flt
from frappe.utils.nestedset import get_descendants_of



@frappe.whitelist()
def generate_mould_assets(
	asset_category,
	company,
	location,
	purchase_date,
	net_purchase_amount,
	item_group=None,
	item_codes=None,
	item_code=None,
	cost_center=None,
	skip_existing_assets=1,
):
	"""Create draft Asset records for Mould item templates and their variants."""
	frappe.has_permission("Asset", "create", throw=True)

	net_purchase_amount = flt(net_purchase_amount)
	if net_purchase_amount <= 0:
		frappe.throw(_("Net Purchase Amount must be greater than zero."))

	if not frappe.db.exists("Asset Category", asset_category):
		frappe.throw(_("Asset Category {0} does not exist.").format(frappe.bold(asset_category)))

	item_groups = _get_item_groups(item_group)
	item_codes = _get_selected_item_codes(item_groups, item_codes, item_code)
	created = []
	skipped = []

	for template_item in item_codes:
		_validate_item_template(template_item, item_groups)

		for item in _get_mould_asset_items(template_item):
			# Create Assets only for template (parent) items; variants are not used for Asset creation.
			asset_item = _get_or_create_asset_item(item, asset_category)

			# Assets should be keyed off the asset-item (fixed asset item), not the template item.
			if _has_existing_asset(asset_item.name) and int(skip_existing_assets):
				skipped.append(asset_item.name)
				continue

			asset = _create_asset(
				item=asset_item,
				asset_category=asset_category,
				company=company,
				location=location,
				purchase_date=purchase_date,
				net_purchase_amount=net_purchase_amount,
				cost_center=cost_center,
			)
			created.append(asset.name)






	return {

		"created": created,
		"skipped": skipped,
	}



def _get_item_groups(item_group=None):
	if not item_group:
		return []

	if not frappe.db.exists("Item Group", item_group):
		frappe.throw(_("Item Group {0} does not exist.").format(frappe.bold(item_group)))

	return [item_group] + get_descendants_of("Item Group", item_group, ignore_permissions=True)


def _get_selected_item_codes(item_groups=None, item_codes=None, item_code=None):
	if item_groups:
		item_codes = frappe.get_all(
			"Item",
			filters={
				"item_group": ["in", item_groups],
				"has_variants": 1,
				"disabled": 0,
			},
			pluck="name",
			order_by="name",
		)
		if not item_codes:
			frappe.throw(_("No template Items found for the selected Item Group."))
		return item_codes

	if isinstance(item_codes, str):
		try:
			item_codes = frappe.parse_json(item_codes)
		except ValueError:
			item_codes = [item_codes]

	if not item_codes and item_code:
		item_codes = [item_code]

	item_codes = [item for item in item_codes or [] if item]
	item_codes = list(dict.fromkeys(item_codes))

	if not item_codes:
		frappe.throw(_("Select at least one Mould Item."))

	return item_codes


def _validate_item_template(item_code, item_groups=None):
	item = frappe.db.get_value(
		"Item",
		item_code,
		["name", "has_variants", "item_group", "disabled"],
		as_dict=True,
	)

	if not item:
		frappe.throw(_("Item {0} does not exist.").format(frappe.bold(item_code)))
	if item.disabled:
		frappe.throw(_("Item {0} is disabled.").format(frappe.bold(item_code)))
	if item_groups and item.item_group not in item_groups:
		frappe.throw(_("Item {0} does not belong to the selected Item Group.").format(frappe.bold(item_code)))
	if not item.has_variants:
		frappe.throw(_("Item {0} must have Has Variants enabled.").format(frappe.bold(item_code)))


def _get_mould_asset_items(template_item):
	"""Return only the template (parent) item.

	Assets should be created from Item Templates (Has Variants enabled), not from variant Items.
	"""
	template = frappe.db.get_value(
		"Item",
		template_item,
		["name", "item_name"],
		as_dict=True,
	)
	return [template]


def _has_existing_asset(item_code):
	return frappe.db.exists(
		"Asset",

		{
			"item_code": item_code,
			"docstatus": ["<", 2],
		},
	)


def _get_or_create_asset_item(template_item, asset_category):
	"""Create/ensure a fixed-asset Item for the given template item.

	Requirement:
	- Item code must be `ASSET-{template_item_code}`
	- Keep the original template item unchanged.
	- Asset item must have `is_fixed_asset=1`.
	"""
	asset_item_code = f"ASSET-{template_item.name}"

	if frappe.db.exists("Item", asset_item_code):
		asset_item = frappe.get_doc("Item", asset_item_code)
	else:
		# Some Item masters require mandatory GST HSN/SAC code fields.
		# Defaulting to a valid code to avoid "HSN/SAC Code is required" errors.

		asset_item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": asset_item_code,
				"item_name": asset_item_code,
				"gst_hsn_code": "84807900",
				"hsn_sac_code": "84807900",
				"item_group": "MOULD",
			}
		)



	changed = False
	for fieldname, value in {
		"is_fixed_asset": 1,
		"is_stock_item": 0,
		"is_non_stock": 1,
		"asset_category": asset_category,
	}.items():
		if asset_item.get(fieldname) != value:
			asset_item.set(fieldname, value)
			changed = True

	if changed:
		# Some validations may be mandatory on Item/Asset masters.
		# This endpoint focuses on generating fixed-asset Items/Assets for moulding.
		# If your environment enforces extra mandatory fields, bypass here.
		asset_item.flags.ignore_mandatory = True
		asset_item.flags.ignore_permissions = True
		asset_item.save()

	# Ensure doc is inserted if it was newly created.
	if asset_item.is_new():
		asset_item.flags.ignore_mandatory = True
		asset_item.flags.ignore_permissions = True
		asset_item.insert()


	return asset_item



def _create_asset(
	item,
	asset_category,
	company,
	location,
	purchase_date,
	net_purchase_amount,
	cost_center=None,
):
	asset = frappe.get_doc(
		{
			"doctype": "Asset",
			"asset_name": "MOULD-{0}".format(item.name),
			"asset_category": asset_category,
			"series": "MOULDS-{0}".format(item.name),
			"item_code": item.name,
			"company": company,
			"location": location,

			"purchase_date": purchase_date,
			"available_for_use_date": purchase_date,
			"net_purchase_amount": net_purchase_amount,
			"purchase_amount": net_purchase_amount,
			"asset_quantity": 1,
			"asset_owner": "Company",
			"asset_type": "Existing Asset",
			"calculate_depreciation": 0,
			"cost_center": cost_center,
			"is_non_stock": 1,
		}

	)

	asset.flags.ignore_mandatory = True
	asset.flags.ignore_permissions = True
	asset.insert(set_name=_get_asset_name(item.name))
	return asset



def _get_asset_name(item_code):
	base_name = "Asset-{0}".format(item_code)
	asset_name = base_name
	counter = 1

	while frappe.db.exists("Asset", asset_name):
		asset_name = "{0}-{1}".format(base_name, counter)
		counter += 1

	return asset_name
