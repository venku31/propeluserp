import frappe
from frappe.desk.search import sanitize_searchfield
from frappe.utils import cint


def _get_work_order(work_order=None, job_card=None):
	if work_order:
		return work_order

	if job_card:
		return frappe.db.get_value("Job Card", job_card, "work_order")

	return None


@frappe.whitelist()
def get_painting_details_from_moulding_job_cards(work_order=None, job_card=None):
	work_order = _get_work_order(work_order, job_card)
	if not work_order:
		return []

	part_numbers = frappe.db.sql(
		"""
		SELECT DISTINCT details.part_number
		FROM `tabMoulding Machine Details` details
		INNER JOIN `tabJob Card` job_card ON job_card.name = details.parent
		WHERE details.parenttype = 'Job Card'
			AND IFNULL(details.part_number, '') != ''
			AND job_card.work_order = %(work_order)s
			AND job_card.operation = 'Moulding'
			AND job_card.docstatus < 2
		ORDER BY details.idx
		""",
		{"work_order": work_order},
		as_dict=True,
	)

	rows = []
	for row in part_numbers:
		item = frappe.get_cached_doc("Item", row.part_number)
		paints = item.get("custom_paints") or []
		paint_items = [paint.paint for paint in paints if paint.paint][:4]

		rows.append(
			{
				"toy_name": item.name,
				"description": item.item_name or item.description,
				"paint_1": paint_items[0] if len(paint_items) > 0 else None,
				"paint_2": paint_items[1] if len(paint_items) > 1 else None,
				"paint_3": paint_items[2] if len(paint_items) > 2 else None,
				"paint_4": paint_items[3] if len(paint_items) > 3 else None,
			}
		)

	return rows


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_moulding_part_number_query(doctype, txt, searchfield, start, page_len, filters):
	searchfield = sanitize_searchfield(searchfield)
	filters = filters or {}
	work_order = _get_work_order(filters.get("work_order"), filters.get("job_card"))

	if not work_order:
		return []

	return frappe.db.sql(
		f"""
		SELECT DISTINCT
			item.name,
			item.item_name,
			item.description
		FROM `tabMoulding Machine Details` details
		INNER JOIN `tabJob Card` job_card ON job_card.name = details.parent
		INNER JOIN `tabItem` item ON item.name = details.part_number
		WHERE details.parenttype = 'Job Card'
			AND IFNULL(details.part_number, '') != ''
			AND job_card.work_order = %(work_order)s
			AND job_card.operation = 'Moulding'
			AND job_card.docstatus < 2
			AND IFNULL(item.disabled, 0) = 0
			AND (
				item.name LIKE %(txt)s
				OR item.item_name LIKE %(txt)s
				OR item.description LIKE %(txt)s
				OR item.{searchfield} LIKE %(txt)s
			)
		ORDER BY item.name
		LIMIT %(start)s, %(page_len)s
		""",
		{
			"work_order": work_order,
			"txt": f"%{txt}%",
			"start": cint(start),
			"page_len": cint(page_len),
		},
	)
