from collections import defaultdict

import frappe
from frappe import _, msgprint
from frappe.utils import cint, comma_and, flt, get_link_to_form, getdate, nowdate, parse_json

from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict
from erpnext.manufacturing.doctype.production_plan.production_plan import (
	ProductionPlan,
	set_default_warehouses,
)


class CustomProductionPlan(ProductionPlan):
	@frappe.whitelist()
	def make_work_order(self):
		from erpnext.manufacturing.doctype.work_order.work_order import get_default_warehouse

		wo_list, po_list = [], []
		subcontracted_po = {}
		default_warehouses = get_default_warehouse(self.company)

		self.make_work_order_for_finished_goods(wo_list, default_warehouses)
		self.make_work_order_for_subassembly_items(wo_list, subcontracted_po, default_warehouses)
		self.make_subcontracted_purchase_order(subcontracted_po, po_list)
		self.show_list_created_message("Work Order", wo_list)
		self.show_list_created_message("Purchase Order", po_list)

		if not wo_list:
			msgprint(_("No Work Orders were created"))

		if not po_list:
			msgprint(_("No Purchase Orders were created"))

	def make_work_order_for_finished_goods(self, wo_list, default_warehouses):
		items_data = self.get_production_items()

		for _key, item in items_data.items():
			if self.sub_assembly_items:
				item["use_multi_level_bom"] = 0

			set_default_warehouses(item, default_warehouses)
			work_order = self.create_work_order(item)
			if work_order:
				wo_list.append(work_order)

	def make_work_order_for_subassembly_items(self, wo_list, subcontracted_po, default_warehouses):
		disable_in_house_work_order = self.disable_in_house_sub_assembly_work_order()

		for row in self.sub_assembly_items:
			if row.type_of_manufacturing == "Subcontract":
				subcontracted_po.setdefault(self.get_subcontracting_supplier(row), []).append(row)
				continue

			if row.type_of_manufacturing == "Material Request":
				continue

			if row.type_of_manufacturing == "In House" and disable_in_house_work_order:
				continue

			work_order_data = {
				"source_warehouse": frappe.get_value("BOM", row.bom_no, "default_source_warehouse"),
				"wip_warehouse": default_warehouses.get("wip_warehouse"),
				"fg_warehouse": default_warehouses.get("fg_warehouse"),
				"scrap_warehouse": default_warehouses.get("scrap_warehouse"),
				"company": self.get("company"),
			}

			if flt(row.qty) <= flt(row.ordered_qty):
				continue

			self.prepare_data_for_sub_assembly_items(row, work_order_data)

			if work_order_data.get("qty") <= 0:
				continue

			work_order = self.create_work_order(work_order_data)
			if work_order:
				wo_list.append(work_order)

	def get_subcontracting_supplier(self, row):
		if row.meta.has_field("custom_supplier"):
			row.supplier = row.get("custom_supplier") or row.get("supplier")

		return row.get("supplier")

	def make_subcontracted_purchase_order(self, subcontracted_po, purchase_orders):
		if not subcontracted_po:
			return

		subcontracted_po = self.calculate_pending_sub_assembly_items(subcontracted_po)

		for supplier, po_list in subcontracted_po.items():
			po = frappe.new_doc("Purchase Order")
			po.company = self.company
			po.supplier = supplier
			po.schedule_date = getdate(po_list[0].schedule_date) if po_list[0].schedule_date else nowdate()
			po.is_subcontracted = 1

			for row in po_list:
				po_data = {
					"fg_item": row.production_item,
					"warehouse": row.fg_warehouse,
					"production_plan_sub_assembly_item": row.name,
					"bom": row.bom_no,
					"production_plan": self.name,
					"fg_item_qty": row.qty,
				}

				for field in [
					"schedule_date",
					"qty",
					"description",
					"production_plan_item",
					"sales_order",
					"sales_order_item",
				]:
					po_data[field] = row.get(field)

				po.append("items", po_data)

			po.set_service_items_for_finished_goods()
			self.set_job_work_charges_item_for_subcontracted_po(po)
			po.set_missing_values()
			po.flags.ignore_mandatory = True
			po.flags.ignore_validate = True
			po.insert()
			purchase_orders.append(po.name)

	def calculate_pending_sub_assembly_items(self, subcontracted_po):
		items_to_remove = defaultdict(list)
		for supplier, items in subcontracted_po.items():
			for item in items:
				if item.qty == item.received_qty:
					items_to_remove[supplier].append(item)
				elif item.received_qty:
					item.qty -= item.received_qty

			subcontracted_po[supplier] = [item for item in items if item not in items_to_remove[supplier]]

		return {key: value for key, value in subcontracted_po.items() if value}

	def set_job_work_charges_item_for_subcontracted_po(self, po):
		job_work_charges_item = frappe.db.get_single_value(
			"Propelus Settings", "job_work_charges_item"
		)

		if not job_work_charges_item:
			return

		item_details = frappe.db.get_value(
			"Item", job_work_charges_item, ["item_name", "stock_uom"], as_dict=True
		)

		for item in po.items:
			if not item.fg_item:
				continue

			item.item_code = job_work_charges_item
			item.item_name = item_details.item_name if item_details else None

			if item_details and item_details.stock_uom:
				item.uom = item_details.stock_uom
				item.stock_uom = item_details.stock_uom

	def show_list_created_message(self, doctype, doc_list=None):
		if not doc_list:
			return

		frappe.flags.mute_messages = False
		doc_list = [get_link_to_form(doctype, p) for p in doc_list]
		msgprint(_("{0} created").format(comma_and(doc_list)))

	def create_work_order(self, item):
		from erpnext.manufacturing.doctype.work_order.work_order import OverProductionError

		if flt(item.get("qty")) <= 0:
			return

		wo = frappe.new_doc("Work Order")
		wo.update(item)
		if not wo.source_warehouse:
			wo.source_warehouse = item.get("fg_warehouse")

		wo.reserve_stock = self.reserve_stock
		wo.planned_start_date = item.get("planned_start_date") or item.get("schedule_date")

		if item.get("warehouse"):
			wo.fg_warehouse = item.get("warehouse")

		wo.set_work_order_operations()
		wo.set_required_items(reset_source_warehouse=True)
		self.add_in_house_sub_assembly_raw_materials(wo, item)

		try:
			wo.flags.ignore_mandatory = True
			wo.flags.ignore_validate = True
			wo.company = self.company
			wo.insert()
			return wo.name
		except OverProductionError:
			pass

	def add_in_house_sub_assembly_raw_materials(self, wo, item):
		if not self.disable_in_house_sub_assembly_work_order():
			return

		sub_assembly_items = self.get_in_house_sub_assembly_items_for_production_item(item)
		if not sub_assembly_items:
			return

		in_house_sub_assembly_items = {row.production_item for row in sub_assembly_items}

		for row in sub_assembly_items:
			self.reduce_required_item_qty(wo, row.production_item, row.qty)
			self.add_bom_raw_materials_to_work_order(
				wo, row.bom_no, row.qty, in_house_sub_assembly_items
			)

		wo.set_available_qty()

	def disable_in_house_sub_assembly_work_order(self):
		return cint(
			frappe.db.get_single_value(
				"Propelus Settings", "disable_in_house_work_order_for_sub_assembly"
			)
		)

	def get_in_house_sub_assembly_items_for_production_item(self, item):
		production_plan_item = item.get("production_plan_item")
		production_item = item.get("production_item")

		return [
			row
			for row in self.sub_assembly_items
			if row.type_of_manufacturing == "In House"
			and row.bom_no
			and row.qty
			and (
				row.production_plan_item == production_plan_item
				or (self.combine_items and row.parent_item_code == production_item)
			)
		]

	def reduce_required_item_qty(self, wo, item_code, qty):
		pending_qty = flt(qty)
		filtered_required_items = []

		for row in wo.required_items:
			if row.item_code != item_code or pending_qty <= 0:
				filtered_required_items.append(row)
				continue

			if flt(row.required_qty) > pending_qty:
				row.required_qty = flt(row.required_qty) - pending_qty
				row.amount = flt(row.rate) * flt(row.required_qty)
				filtered_required_items.append(row)
				pending_qty = 0
			else:
				pending_qty -= flt(row.required_qty)

		wo.set("required_items", filtered_required_items)

	def add_bom_raw_materials_to_work_order(self, wo, bom_no, qty, in_house_sub_assembly_items):
		item_dict = get_bom_items_as_dict(bom_no, self.company, qty=qty, fetch_exploded=0)

		for item in sorted(item_dict.values(), key=lambda d: d["idx"] or float("inf")):
			if item.item_code in in_house_sub_assembly_items:
				continue

			self.add_or_update_required_item(wo, item)

	def add_or_update_required_item(self, wo, item):
		operation = None
		if wo.get("operations") and len(wo.operations) == 1:
			operation = wo.operations[0].operation

		item_operation = item.operation or operation

		for row in wo.required_items:
			if row.item_code != item.item_code or row.operation != item_operation:
				continue

			row.required_qty = flt(row.required_qty) + flt(item.qty)
			row.amount = flt(row.rate) * flt(row.required_qty)
			return

		wo.append(
			"required_items",
			{
				"rate": item.rate,
				"amount": flt(item.rate) * flt(item.qty),
				"operation": item_operation,
				"item_code": item.item_code,
				"item_name": item.item_name,
				"stock_uom": item.stock_uom,
				"description": item.description,
				"allow_alternative_item": item.allow_alternative_item,
				"required_qty": item.qty,
				"source_warehouse": wo.source_warehouse,
				"include_item_in_manufacturing": item.include_item_in_manufacturing,
				"operation_row_id": item.operation_row_id,
			},
		)

	def set_default_supplier_for_subcontracting_order(self):
		items = [
			d.production_item for d in self.sub_assembly_items if d.type_of_manufacturing == "Subcontract"
		]

		if not items:
			return

		default_supplier = frappe._dict(
			frappe.get_all(
				"Item Default",
				fields=["parent", "default_supplier"],
				filters={"parent": ("in", items), "default_supplier": ("is", "set")},
				as_list=1,
			)
		)

		if not default_supplier:
			return

		for row in self.sub_assembly_items:
			if row.type_of_manufacturing != "Subcontract":
				continue

			row.supplier = default_supplier.get(row.production_item)
			if row.meta.has_field("custom_supplier"):
				row.custom_supplier = row.supplier


@frappe.whitelist()
def make_work_order(doc=None, name=None):
	if doc:
		doc = parse_json(doc) if isinstance(doc, str) else doc
		if isinstance(doc, dict):
			production_plan = frappe.get_doc(doc)
		else:
			production_plan = frappe.get_doc("Production Plan", doc)
	elif name:
		production_plan = frappe.get_doc("Production Plan", name)
	else:
		frappe.throw(_("Production Plan is required"))

	production_plan.make_work_order()
	production_plan.reload()
	return production_plan.as_dict()
