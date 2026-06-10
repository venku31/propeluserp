// Filter mould_asset on Stock Entry to show only submitted Assets

frappe.ui.form.on("Stock Entry", {
	onload: function (frm) {
		if (!frm.doc) return;
		frm.set_query("mould_asset", () => {
			return {
				filters: {
					docstatus: 1,
				},
			};
		});
	},

	// In case field is set after load
	rest_refresh: function (frm) {
		if (frm.set_query) {
			frm.set_query("mould_asset", () => {
				return {
					filters: {
						docstatus: 1,
					},
				};
			});
		}
	},
});

