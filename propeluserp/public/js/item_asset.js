frappe.ui.form.on("Item", {
	refresh(frm) {
		frm.add_custom_button(__("Generate Mould Assets"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Generate Mould Assets"),
				fields: [
					{
						fieldname: "item_group",
						fieldtype: "Link",
						label: __("Item Group"),
						options: "Item Group",
						reqd: 1,
						default: frm.doc.item_group || "Mould",
					},
					{
						fieldname: "asset_category",
						fieldtype: "Link",
						label: __("Asset Category"),
						options: "Asset Category",
						reqd: 1,
					},
					{
						fieldname: "company",
						fieldtype: "Link",
						label: __("Company"),
						options: "Company",
						reqd: 1,
						default: frappe.defaults.get_user_default("Company"),
					},
					{
						fieldname: "location",
						fieldtype: "Link",
						label: __("Location"),
						options: "Location",
						reqd: 1,
					},
					{
						fieldname: "purchase_date",
						fieldtype: "Date",
						label: __("Purchase Date"),
						reqd: 1,
						default: frappe.datetime.get_today(),
					},
					{
						fieldname: "net_purchase_amount",
						fieldtype: "Currency",
						label: __("Net Purchase Amount"),
						reqd: 1,
						default: 1,
					},
					{
						fieldname: "cost_center",
						fieldtype: "Link",
						label: __("Cost Center"),
						options: "Cost Center",
						get_query() {
							return {
								filters: {
									company: dialog.get_value("company"),
									is_group: 0,
								},
							};
						},
					},
					{
						fieldname: "skip_existing_assets",
						fieldtype: "Check",
						label: __("Skip Items That Already Have Assets"),
						default: 1,
					},
				],
				primary_action_label: __("Generate"),
				primary_action(values) {
					dialog.disable_primary_action();
					frappe.call({
						method: "propeluserp.api.item_asset.generate_mould_assets",
						args: values,
						freeze: true,
						freeze_message: __("Generating Assets..."),
					}).then((response) => {
						const result = response.message || {};
						const created = result.created || [];
						const skipped = result.skipped || [];
						const message = [
							created.length ? __("Created Assets: {0}", [created.join(", ")]) : __("No Assets created."),
							skipped.length ? __("Skipped Items: {0}", [skipped.join(", ")]) : "",
						].filter(Boolean).join("<br>");

						frappe.msgprint({
							title: __("Mould Assets Generated"),
							message,
							indicator: created.length ? "green" : "orange",
						});
						dialog.hide();
					}).always(() => {
						dialog.enable_primary_action();
					});
				},
			});

			dialog.show();
		}, __("Create"));
	},
});
