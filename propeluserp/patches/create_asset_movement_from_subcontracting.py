import frappe


def create_server_script(name, script):
    if frappe.db.exists("Server Script", name):
        return
    ss = frappe.get_doc({
        "doctype": "Server Script",
        "name": name,
        "script_type": "DocType Event",
        "reference_doctype": "Subcontracting Order",
        "event": "on_submit",
        "enabled": 1,
        "python": script,
    })
    ss.insert(ignore_permissions=True)


def execute():
    # No-op: server script creation removed. Handlers are provided via hooks.
    return
