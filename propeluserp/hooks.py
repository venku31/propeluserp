app_name = "propeluserp"
app_title = "Propeluserp"
app_publisher = "Propelus"
app_description = "Propelus ERP"
app_email = "venku31@gmail.com"
app_license = "mit"

# Fixtures: ensure custom fields are installed from the app instead of patches
fixtures = [
	{"doctype": "Custom Field",
		"filters": [
			[
				"name",
				"in",
				[
					"Stock Entry-custom_column_break_atmq5",
					"Job Card-custom_section_break_3ko4m",
					"Job Card-custom_machine_details",
					"Job Card-custom_section_break_g0ufl",
					"Job Card-custom_machine",
					"Job Card-custom_column_break_kh5ig",
					"Job Card-custom_mould",
					"Job Card-custom_column_break_ugv7n",
					"Job Card-custom_daily_moulding_details",
					"Job Card-custom_section_break_zv4qv",
					"Job Card-custom_moulding_machine_details",
					"Job Card-custom_painting_details",
					"Job Card-custom_daily_painting_details",
					"Job Card-custom_section_break_vszmr",
					"Job Card-custom_painting_det",
					"Job Card-custom_assembly_details",
					"Job Card-custom_add_daily_assembly_production",
					"Job Card-custom_section_break_w6xzq",
					"Job Card-custom_assembly_detail",
					"Job Card-inventory_dimension",
					"Job Card-storage_location",
					"Item-custom_moulding_rm_primary",
					"Item-custom_moulding_rm_secondary",
					"Item-custom_moulding_mb_primary",
					"Item-custom_moulding_mb_secondary",
					"Item-custom_paints",
					"Subcontracting Order-mould_asset",
					"Subcontracting Order-mould_target_location",
					"Subcontracting Order-asset_movement",
					"Production Plan-custom_supplier",
					"Production Plan Sub Assembly Item-custom_supplier",
					"Stock Entry-custom_column_break_0bkfh",
					"Stock Entry-mould_target_location",
					"Stock Entry-custom_mould_assets",
					"Stock Entry-asset_movement",
				],
			]
		],
	}
	,
	{"doctype": "Property Setter",
		"filters": [
			[
				"name",
				"in",
				[
					"BOM-with_operations-allow_on_submit",
					"BOM-operations-allow_on_submit",
					"BOM-items-allow_on_submit",
					"BOM-raw_material_cost-allow_on_submit",
					"BOM-operating_cost-allow_on_submit",
					"BOM-operating_cost-allow_on_submit",
					"BOM-base_secondary_items_cost-allow_on_submit",
					"BOM-secondary_items_cost-allow_on_submit",
					"BOM-base_raw_material_cost-allow_on_submit",
					"BOM-raw_material_cost-allow_on_submit",
					"BOM-items-allow_on_submit",
					"BOM-operations-allow_on_submit",
					"BOM-with_operations-allow_on_submit",
					"BOM-transfer_material_against-allow_on_submit",
					"BOM Item-operation-allow_on_submit",
					"BOM Item-uom-allow_on_submit",
					"Production Plan Sub Assembly Item-supplier-hidden",
					"Job Card-barcode-hidden",
					"Job Card-main-field_order",
					"Job Card-naming_series-default",
					"Job Card-naming_series-options",
					"Job Card-section_break_21-depends_on",
					"Job Card-section_break_21-hidden",
					"Stock Entry Detail-allow_zero_valuation_rate-default",
				],
			],
		],
	}
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "propeluserp",
# 		"logo": "/assets/propeluserp/logo.png",
# 		"title": "Propeluserp",
# 		"route": "/propeluserp",
# 		"has_permission": "propeluserp.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/propeluserp/css/propeluserp.css"
# app_include_js = "/assets/propeluserp/js/propeluserp.js"

# include js, css files in header of web template
# web_include_css = "/assets/propeluserp/css/propeluserp.css"
# web_include_js = "/assets/propeluserp/js/propeluserp.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "propeluserp/public/scss/website"
app_include_js = ["/assets/propeluserp/js/bom_override.js"]
# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "propeluserp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "propeluserp.utils.jinja_methods",
# 	"filters": "propeluserp.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "propeluserp.install.before_install"
# after_install = "propeluserp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "propeluserp.uninstall.before_uninstall"
# after_uninstall = "propeluserp.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "propeluserp.utils.before_app_install"
# after_app_install = "propeluserp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "propeluserp.utils.before_app_uninstall"
# after_app_uninstall = "propeluserp.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "propeluserp.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "propeluserp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events
doctype_js = {
	"BOM": "public/js/bom_override.js",
	"Item": "public/js/item_asset.js",
	"Job Card": "public/js/job_card.js",
	"Production Plan": "public/js/production_plan.js",
	"Stock Entry": "public/js/stock_entry_asset_filters.js",
}

override_whitelisted_methods = {
	"frappe.desk.form.linked_with.cancel_all_linked_docs":
		"propeluserp.api.bom_cancel.cancel_all_linked_docs",
}

override_doctype_class = {
	"Production Plan": "propeluserp.overrides.production_plan.CustomProductionPlan",
}

doc_events = {
	"BOM": {
		"before_cancel": "propeluserp.propeluserp.doctype.propelus_settings.propelus_settings.apply_ignore_links_for_bom",

		"after_cancel": "propeluserp.propeluserp.doctype.propelus_settings.propelus_settings.apply_ignore_links_for_bom",
		"on_trash": "propeluserp.propeluserp.doctype.propelus_settings.propelus_settings.apply_ignore_links_for_bom",
	},
	"Stock Entry": {
		"before_save": "propeluserp.api.asset_movement_handler.on_stock_entry_before_save",
		"validate": "propeluserp.api.asset_movement_handler.on_stock_entry_validate",
		"on_submit": "propeluserp.api.asset_movement_handler.on_stock_entry_submit",
		"before_cancel": "propeluserp.api.asset_movement_handler.on_stock_entry_cancel",
	},
	"Job Card": {
		"before_validate": "propeluserp.api.job_card_completion.sync_completed_qty_from_custom_details",
		"validate": "propeluserp.api.job_card_completion.sync_completed_qty_from_custom_details",
		"before_save": "propeluserp.api.job_card_completion.sync_completed_qty_from_custom_details",
		"before_submit": "propeluserp.api.job_card_completion.sync_completed_qty_from_custom_details",
	},
	"Work Order": {
		"validate": "propeluserp.api.work_order.sync_required_item_operations_from_bom",
		"before_save": "propeluserp.api.work_order.sync_required_item_operations_from_bom",
		"before_submit": "propeluserp.api.work_order.sync_required_item_operations_from_bom",
	},
	"Production Plan": {
		"before_validate": "propeluserp.api.production_plan.sync_custom_supplier",
		"validate": "propeluserp.api.production_plan.sync_custom_supplier",
		"before_save": "propeluserp.api.production_plan.sync_custom_supplier",
		"before_submit": "propeluserp.api.production_plan.sync_custom_supplier",
	},
	"Asset Movement": {
		"before_cancel": "propeluserp.propeluserp.doctype.propelus_settings.propelus_settings.apply_ignore_links_for_asset_movement",
		"on_trash": "propeluserp.propeluserp.doctype.propelus_settings.propelus_settings.apply_ignore_links_for_asset_movement",
	},

}


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"propeluserp.tasks.all"
# 	],
# 	"daily": [
# 		"propeluserp.tasks.daily"
# 	],
# 	"hourly": [
# 		"propeluserp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"propeluserp.tasks.weekly"
# 	],
# 	"monthly": [
# 		"propeluserp.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "propeluserp.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "propeluserp.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "propeluserp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "propeluserp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["propeluserp.utils.before_request"]
# after_request = ["propeluserp.utils.after_request"]

# Job Events
# ----------
# before_job = ["propeluserp.utils.before_job"]
# after_job = ["propeluserp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"propeluserp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
