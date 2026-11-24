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
		self.suppliers = [x.docname for x in self.supplier]
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

		# make bank account
		hdfc_bank_acc = frappe.db.get_all("Account", {"account_name": "HDFC Current", "company": company}, pluck="name")
		if not hdfc_bank_acc:
			group_bank_acc = frappe.db.get_all("Account", {"account_name": "Bank Accounts", "account_type": "Bank", "account_category": "Cash and Cash Equivalents"}, pluck="name")[0]
			bank_acc = frappe.new_doc("Account")
			bank_acc.account_name = "HDFC Current"
			bank_acc.account_type = "Bank"
			bank_acc.parent_account = group_bank_acc
			bank_acc.company = company
			bank_acc.save()
			bank_acc.reload()
			frappe.db.set_value("Company", company, "default_bank_account", bank_acc.name)
		else:
			frappe.db.set_value("Company", company, "default_bank_account", hdfc_bank_acc[0])

		frappe.db.commit()


	def make_100_sales_invoice(self):
		import datetime
		import random

		from erpnext.accounts.utils import get_fiscal_year

		self.update_stage("Generating sales invoices...")
		company = frappe.db.get_all("Company", pluck="name")[0]
		fy = get_fiscal_year()
		delta = fy.year_end_date - fy.year_start_date
		dates = [fy.year_start_date + datetime.timedelta(x) for x in range(delta.days + 1)]
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
			self.update_stage(f"Making Sales Invoice {si.name}")

		self.update_stage("Committing...")
		frappe.db.commit()


	def make_100_payment_entry(self):
		import datetime
		import random

		from erpnext.accounts.utils import get_fiscal_year

		self.update_stage("Generating payment entries...")
		company = frappe.db.get_all("Company", pluck="name")[0]
		fy = get_fiscal_year()
		delta = fy.year_end_date - fy.year_start_date
		dates = [fy.year_start_date + datetime.timedelta(x) for x in range(delta.days + 1)]
		bank_acc = frappe.db.get_all("Account", {"account_name": "HDFC Current", "company": company}, pluck="name")[0]
		cash_acc = frappe.db.get_all("Account", {"account_name": "Cash", "company": company}, pluck="name")[0]
		for x in range(100):
			pe = frappe.new_doc("Payment Entry")
			pe.company = company
			pe.customer = random.choice(self.customers)
			pe.posting_date = random.choice(dates)
			pe.payment_type = "Receive"

			mode_of_payment = random.choice(["Cash", "Wire Transfer"])
			pe.mode_of_payment = mode_of_payment
			if mode_of_payment == "Cash":
				pe.paid_to = cash_acc
			else:
				pe.paid_to = bank_acc

			pe.party_type = "Customer"
			pe.party = random.choice(self.customers)

			pe.reference_no = random.choice(range(10000000))
			pe.reference_date = random.choice(dates)
			paid_amount = random.randrange(100, 1000, 1)
			pe.paid_amount = paid_amount
			pe.received_amount = paid_amount
			pe.save().submit()
			self.update_stage(f"Making payment entry {pe.name}")

		self.update_stage("Committing...")
		frappe.db.commit()


	@frappe.whitelist()
	def generate(self):
		self.generate_masters()

		# Sales Invoice
		frappe.enqueue_task(
			method="data_generator.data_generator.doctype.data_generator.data_generator.make_100_batches_of_si",
			doc=self,
		)
		# Payment Entry
		frappe.enqueue_task(
			method="data_generator.data_generator.doctype.data_generator.data_generator.make_100_batches_of_pe",
			doc=self,
		)


def make_100_batches_of_si(doc):
	for x in range(100):
		doc.make_100_sales_invoice()

def make_100_batches_of_pe(doc):
	for x in range(100):
		doc.make_100_payment_entry()
