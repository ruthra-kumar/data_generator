# Copyright (c) 2026, Ruthra and contributors
# For license information, please see license.txt

import frappe
import erpnext
from frappe.model.document import Document


class DataGenerator(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from data_generator.data_generator.doctype.generator_item.generator_item import GeneratorItem
		from frappe.types import DF

		cost_center: DF.Table[GeneratorItem]
		customer: DF.Table[GeneratorItem]
		item: DF.Table[GeneratorItem]
		supplier: DF.Table[GeneratorItem]
	# end: auto-generated types

	_DOCTYPE_NAME = "Data Generator"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.customers = [x.docname for x in self.customer]
		self.items = [x.docname for x in self.item]
		self.cc = [x.docname for x in self.cost_center]


	def update_stage(self, msg):
		if task := frappe.get_current_task():
			task.update_stage(stage=msg)

	def generate_masters(self):
		self.update_stage("Generating customers...")
		existing_customers = frappe.db.get_all("Customer", pluck="name")
		for name in self.customers:
			if name not in existing_customers:
				cust = frappe.new_doc("Customer")
				cust.customer_name = name
				cust.customer_type = "Individual"
				cust.customer_group = "Individual"
				cust.save()

		self.update_stage("Generating items...")
		existing_items = frappe.db.get_all("Item", pluck="name")
		for name in self.items:
			if name not in existing_items:
				itm = frappe.new_doc("Item")
				itm.item_code = name
				itm.item_group = "Products"
				itm.stock_uom = "Nos"
				itm.is_stock_item = False
				itm.save()

		company = frappe.db.get_all("Company", pluck="name")[0]

		self.update_stage("Generating cost centers...")
		# 'Main' is available on normal installation
		main_cc_name = frappe.db.get_all("Cost Center", {"cost_center_name": "Main", "company": company})[0]
		main_cc = frappe.get_doc("Cost Center", main_cc_name)
		existing_costcenters = frappe.db.get_all("Cost Center", pluck="cost_center_name")
		for name in self.cc:
			if name not in existing_costcenters:
				cc = frappe.new_doc("Cost Center")
				cc.cost_center_name = name
				cc.parent_cost_center = main_cc.parent_cost_center
				cc.save()

	def make_100_sales_invoice(self):
		import datetime
		import random

		from erpnext.accounts.utils import get_fiscal_year

		self.update_stage("Generating sales invoices...")
		company = frappe.db.get_all("Company", pluck="name")[0]
		fy = get_fiscal_year()
		delta = fy.year_end_date - fy.year_start_date
		dates = [fy.year_start_date + datetime.timedelta(x) for x in range(delta.days + 1)]
		# customers = frappe.db.get_all("Customer", pluck="name")
		items = frappe.db.get_all("Item", pluck="name")
		for x in range(100):
			si = frappe.new_doc("Sales Invoice")
			si.company = company
			si.set_posting_time = True
			si.customer = random.choice(self.customers)
			si.posting_date = random.choice(dates)
			si.append(
				"items",
				{
					"item_code": random.choice(self.items),
					"rate": random.randrange(100, 1000, 1),
					"qty": random.randrange(1, 10, 1),
				},
			)
			si.save().submit()
			self.update_stage(f"Sales Invoice {si.name} made")

		self.update_stage("Committing...")
		frappe.db.commit()

	@frappe.whitelist()
	def generate(self):
		frappe.enqueue_task(
			method="data_generator.data_generator.doctype.data_generator.data_generator.make_100_batches_of_si",
			doc=self,
		)

def make_100_batches_of_si(doc):
	doc.generate_masters()
	for x in range(100):
		doc.make_100_sales_invoice()
