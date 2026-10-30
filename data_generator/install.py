import frappe

def after_install():
	# make default masters
	customers = ["John Doe", "Jane Doe", "Smith", "Yardley", "Jensen"]
	suppliers = ["Local Supplier", "Xerox", "Wesley", "MSS Couriers", "L&T Infra"]
	items = ["Notebook", "Type-C charger", "Water bottle", "Shoe", "Handbag"]
	cc = ["North Wing", "South Wing", "East Wing", "West Wing", "Old headquarters"]

	doc = frappe.get_doc("Data Generator")
	doc.customer = []
	for x in customers:
		doc.append("customer", {"docname": x})

	doc.supplier = []
	for x in suppliers:
		doc.append("supplier", {"docname": x})

	doc.item = []
	for x in items:
		doc.append("item", {"docname": x})

	doc.cost_center = []
	for x in cc:
		doc.append("cost_center", {"docname": x})

	doc.save()
