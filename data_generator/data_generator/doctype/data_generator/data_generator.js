// Copyright (c) 2026, Ruthra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Generator", {
	refresh(frm) {
	    frm.add_custom_button(__("Generate"), () => {
		frappe.call({
		    method: "generate",
		    doc: frm.doc,
		    callback: function(r) { }
		});
	    });
	},
});
