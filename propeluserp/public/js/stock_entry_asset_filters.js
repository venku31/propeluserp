// Filter mould assets on Stock Entry to show only submitted Assets

frappe.ui.form.on("Stock Entry", {
	onload: function (frm) {
		// Ensure asset_movement link is blank on draft/new docs.
		// This prevents linking during "create from Subcontract Order" flows.
		if (frm && frm.doc && cint(frm.doc.docstatus) < 1) {
			try {
				frm.set_value("asset_movement", "");
				frm.refresh_field("asset_movement");
			} catch (e) {
				// field might not exist in some setups
			}
		}

		if (!frm.doc) return;

		// Backward compatibility: if single field still exists.
		if (frm.set_query) {
			frm.set_query("mould_asset", () => {
				return {
						filters: {
							docstatus: 1,
						},
				};
			});
		}

		// New child table filtering (custom field/table name)
		if (
			frm.set_query &&
			frm.fields_dict &&
			(frm.fields_dict.custom_mould_assets || frm.fields_dict.mould_assets)
		) {
			const gridField = frm.fields_dict.custom_mould_assets
				? "custom_mould_assets"
				: "mould_assets";
			frm.set_query("mould_asset", gridField, () => {
				return {
					filters: {
						docstatus: 1,
					},
				};
			});
		}

		// Auto-fill current_location on mould_asset selection in child table.
		const trySetRowCurrentLocation = async (gridField, row, assetName) => {
			if (!assetName || !row) return;

			try {
				const res = await new Promise((resolve) => {
					frappe.call({
						method:
							"propeluserp.api.asset_movement_handler.get_asset_current_location",
						args: { asset: assetName },
						freeze: false,
						callback: (r) => resolve(r),
					});
				});

				const data = res && res.message ? res.message : {};
				const candidates = [
					"current_location",
					"mould_current_location",
					"source_location",
				];
				const fieldToSet =
					candidates.find((f) => row[f] !== undefined) || "current_location";

				const value = data.current_location || data.location || "";
				row.set(fieldToSet, value || "");
				frm.refresh_field(gridField);
			} catch (e) {
				// Fail silently; user can manually fill.
			}
		};

		const gridField = frm.fields_dict.custom_mould_assets
			? "custom_mould_assets"
			: frm.fields_dict.mould_assets
				? "mould_assets"
				: null;

		if (gridField && frm.fields_dict[gridField] && frm.fields_dict[gridField].grid) {
			const grid = frm.fields_dict[gridField].grid;

			// Avoid double-binding
			if (!grid.__mould_current_location_bound) {
				grid.__mould_current_location_bound = true;

				grid.on("fieldchange", async (gridRow, fieldname) => {
					try {
						if (fieldname !== "mould_asset") return;
						const rowDoc = gridRow && gridRow.doc ? gridRow.doc : null;
						if (!rowDoc) return;
						await trySetRowCurrentLocation(gridField, rowDoc, rowDoc.mould_asset);
					} catch (e) {}
				});

				grid.on("render", () => {
					try {
						// Also attempt to fill already-selected mould assets on render
						const rows = grid.grid_rows || [];
						rows.forEach((gr) => {
							const rowDoc = gr && gr.doc ? gr.doc : null;
							if (rowDoc && rowDoc.mould_asset) {
								trySetRowCurrentLocation(gridField, rowDoc, rowDoc.mould_asset);
							}
						});
					} catch (e) {}
				});
			}
		}
	},

	refresh: function (frm) {
		if (
			frm.set_query &&
			frm.fields_dict &&
			(frm.fields_dict.custom_mould_assets || frm.fields_dict.mould_assets)
		) {
			const gridField = frm.fields_dict.custom_mould_assets
				? "custom_mould_assets"
				: "mould_assets";
			frm.set_query("mould_asset", gridField, () => {
				return {
					filters: {
						docstatus: 1,
					},
				};
			});
		}
	},
});

