#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import traceback
from datawald_agency import Agency
from datawald_connector import DatawaldConnector
from suitetalk_connector import SOAPConnector
from datetime import datetime, timedelta
from pytz import timezone


class NSAgency(Agency):
    def __init__(self, logger, **setting):
        self.logger = logger
        self.setting = setting
        self.soap_connector = SOAPConnector(logger, **setting)
        self.datawald = DatawaldConnector(logger, **setting)
        Agency.__init__(self, logger, datawald=self.datawald)

        self.map = setting.get("TXMAP", {})
        self.join = setting.get("JOIN", {"base": [], "lines": []})

    @property
    def payment_methods(self):
        return self.setting.get("PAYMENT_METHODS", {"####": "Net Terms"})

    @property
    def ship_methods(self):
        return self.setting.get("SHIP_METHODS", {"####": "Will Call"})

    @property
    def countries(self):
        return self.setting.get("COUNTRIES", {"US": "_unitedStates"})

    def get_term(self, payment_method):
        terms = self.setting.get(
            "TERMS", {"Net 15": ["Net Terms"], "Credit Card": ["Visa"]}
        )

        for term, payment_methods in terms.items():
            if payment_method in payment_methods:
                return term
        return None

    def get_record_type(self, tx_type):
        data_type = {
            "order": "salesOrder",
            "invoice": "invoice",
            "purchaseorder": "purchaseOrder",
            "quote": "estimate",
            "opportunity": "opportunity",
            "rma": "returnAuthorization",
            "itemfulfillment": "itemFulfillment",
            "itemreceipt": "itemReceipt",
            "billcredit": "vendorCredit",
            "payment": "vendorPayment",
            "customer": "customer",
            "vendor": "vendor",
            "product": "product",
            "inventory": "inventory",
            "inventorylot": "inventoryLot",
            "pricelevel": "priceLevel",
        }
        return data_type.get(tx_type)

    def get_records(self, funct, record_type, **params):
        try:
            current = datetime.now(tz=timezone(self.setting.get("TIMEZONE", "UTC")))
            hours = params.get("hours", 0.0)
            while True:
                self.logger.info(params)
                records = funct(record_type, **params)
                end = datetime.strptime(
                    params.get("cut_date"), "%Y-%m-%d %H:%M:%S"
                ) + timedelta(hours=hours)
                end = end.replace(tzinfo=timezone(self.setting.get("TIMEZONE", "UTC")))
                if hours == 0.0:
                    return records
                elif len(records) >= 1 or end >= current:
                    return records
                else:
                    params["hours"] = params["hours"] + hours
        except Exception:
            log = traceback.format_exc()
            self.logger.exception(log)
            raise

    def transform_data(self, record, metadatas):
        return super(NSAgency, self).transform_data(
            record, metadatas, get_cust_value=self.get_custom_field_value
        )

    def get_custom_field_value(self, record, script_id):
        value = None
        if record["customFieldList"] is None:
            return value
        _custom_fields = list(
            filter(
                lambda custom_field: (
                    custom_field["scriptId"] == script_id.replace("@", "")
                ),
                record["customFieldList"]["customField"],
            )
        )
        if len(_custom_fields) == 1:
            value = _custom_fields[0]["value"]
        return value

    def tx_transactions_src(self, **kwargs):
        try:
            record_type = self.get_record_type(kwargs.get("tx_type"))
            params = {
                "vendor_id": kwargs.get("vendor_id"),
                "subsidiary": kwargs.get("subsidiary"),
                "cut_date": kwargs.get("cut_date").strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": datetime.now(
                    tz=timezone(self.setting.get("TIMEZONE", "UTC"))
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "item_detail": kwargs.get("item_detail", False),
                "limit": int(kwargs.get("limit", 100)),
                "hours": float(kwargs.get("hours", 0)),
            }

            raw_transactions = self.get_records(
                self.soap_connector.get_transactions, record_type, **params
            )

            transactions = list(
                map(
                    lambda raw_transaction: self.tx_transaction_src(
                        raw_transaction, **kwargs
                    ),
                    raw_transactions,
                )
            )

            return transactions
        except Exception:
            self.logger.info(kwargs)
            log = traceback.format_exc()
            self.logger.exception(log)
            raise

    def tx_transaction_src(self, raw_transaction, **kwargs):
        tx_type = kwargs.get("tx_type")
        transaction = {
            "src_id": raw_transaction[self.setting["src_metadata"][tx_type]["src_id"]],
            "created_at": raw_transaction[
                self.setting["src_metadata"][tx_type]["created_at"]
            ],
            "updated_at": raw_transaction[
                self.setting["src_metadata"][tx_type]["updated_at"]
            ],
        }
        try:
            transaction.update(
                {
                    "data": self.transform_data(
                        raw_transaction, self.map.get(self.get_record_type(tx_type))
                    )
                }
            )
        except Exception:
            log = traceback.format_exc()
            transaction.update(
                {"tx_status": "F", "tx_note": log, "data": raw_transaction}
            )
            self.logger.exception(log)

        return transaction

    def tx_assets_src(self, **kwargs):
        try:
            params = {
                "cut_date": kwargs.get("cut_date").strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": datetime.now(
                    tz=timezone(self.setting.get("TIMEZONE", "UTC"))
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "limit": int(kwargs.get("limit", 100)),
                "hours": float(kwargs.get("hours", 0)),
                "subsidiary": kwargs.get("subsidiary"),
                "last_qty_available_change": kwargs.get(
                    "last_qty_available_change", True
                ),
            }

            if kwargs.get("item_types"):
                params.update({"item_types": kwargs.get("item_types")})

            record_type = self.get_record_type(kwargs.get("tx_type"))
            assert record_type is not None, f"{kwargs.get('tx_type')} is not supported."

            if record_type == "product":
                params.update(
                    {
                        "active_only": kwargs.get("active_only", False),
                        "vendor_name": kwargs.get("vendor_name"),
                    }
                )
                kwargs.update({"metadatas": self.get_product_metadatas(**kwargs)})

            raw_assets = self.get_records(
                self.soap_connector.get_items, record_type, **params
            )

            assets = list(
                map(
                    lambda raw_asset: self.tx_asset_src(raw_asset, **kwargs),
                    raw_assets,
                )
            )
            return assets
        except Exception:
            self.logger.info(kwargs)
            log = traceback.format_exc()
            self.logger.exception(log)
            raise

    def tx_asset_src(self, raw_asset, **kwargs):
        tx_type = kwargs.get("tx_type")
        asset = {
            "src_id": raw_asset[self.setting["src_metadata"][tx_type]["src_id"]],
            "created_at": raw_asset[
                self.setting["src_metadata"][tx_type]["created_at"]
            ],
            "updated_at": raw_asset[
                self.setting["src_metadata"][tx_type]["updated_at"]
            ],
        }
        try:
            if tx_type == "product":
                data = self.transform_data(raw_asset, kwargs.get("metadatas"))
            else:
                data = self.transform_data(
                    raw_asset, self.map.get(self.get_record_type(tx_type))
                )

            if tx_type == "inventory":
                inventory = data.get("locations")
                asset.update(
                    {
                        "data": {"inventory": inventory},
                    }
                )
            elif tx_type == "inventorylot":
                inventorylots = list(
                    map(
                        lambda inventory_number: self.tx_inventorylot_src(
                            inventory_number
                        ),
                        data.get("inventoryNumbers", []),
                    )
                )
                asset.update(
                    {
                        "data": {"inventorylots": inventorylots},
                    }
                )
            elif tx_type == "pricelevel":
                # pricelevels path in NetSuite: item.pricingMatrix.pricing
                pricelevels = list(
                    map(
                        lambda pricelevel: self.tx_pricelevel_src(pricelevel),
                        data.get("pricelevels", []),
                    )
                )
                asset.update({"data": {"pricelevels": pricelevels}})
            else:
                asset.update({"data": data})

        except Exception:
            log = traceback.format_exc()
            asset.update({"tx_status": "F", "tx_note": log})
            self.logger.exception(log)
        return asset

    def tx_inventorylot_src(self, inventory_number):
        if inventory_number["status"] == "Not in Stock":
            inventory_number["locations"] = []

        inventory_number["locations"] = [
            location
            for location in inventory_number["locations"]
            if sum(value for value in location.values() if type(value) != str) != 0
        ]

        return inventory_number

    def tx_pricelevel_src(self, pricelevel):
        return {
            "name": pricelevel["priceLevel"]["name"],
            "pricelist": [
                {
                    "price": str(price["value"]),
                    "qty": price["quantity"] if price["quantity"] is not None else 1,
                }
                for price in pricelevel["priceList"]["price"]
            ],
        }

    def tx_persons_src(self, **kwargs):
        try:
            params = {
                "cut_date": kwargs.get("cut_date").strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": datetime.now(
                    tz=timezone(self.setting.get("TIMEZONE", "UTC"))
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "limit": int(kwargs.get("limit", 100)),
                "hours": float(kwargs.get("hours", 0)),
                "subsidiary": kwargs.get("subsidiary")
            }

            record_type = self.get_record_type(kwargs.get("tx_type"))
            assert record_type is not None, f"{kwargs.get('tx_type')} is not supported."

            raw_persons = self.get_records(
                self.soap_connector.get_persons, record_type, **params
            )

            persons = list(
                map(
                    lambda raw_person: self.tx_person_src(raw_person, **kwargs),
                    raw_persons,
                )
            )

            return persons
        except Exception:
            log = traceback.format_exc()
            self.logger.exception(log)
            raise

    def tx_person_src(self, raw_person, **kwargs):
        tx_type = kwargs.get("tx_type")
        person = {
            "src_id": raw_person[self.setting["src_metadata"][tx_type]["src_id"]],
            "created_at": raw_person[
                self.setting["src_metadata"][tx_type]["created_at"]
            ],
            "updated_at": raw_person[
                self.setting["src_metadata"][tx_type]["updated_at"]
            ],
        }
        try:
            person.update(
                {"data": self.transform_data(raw_person, self.map.get(tx_type))}
            )
        except Exception:
            log = traceback.format_exc()
            person.update({"tx_status": "F", "tx_note": log})
            self.logger.exception(log)
        return person

    def validate_customer_data(self, person, **kwargs):
        assert person["data"].get("email"), f"{person['src_id']} email is null in data."

    def validate_vendor_data(self, person, **kwargs):
        assert person["data"].get("email"), f"{person['src_id']} email is null in data."

    def tx_transaction_tgt(self, transaction):
        if transaction["data"].get("paymentMethod"):
            transaction["data"]["paymentMethod"] = self.payment_methods[
                transaction["data"]["paymentMethod"]
            ]
            transaction["data"]["terms"] = self.get_term(
                transaction["data"]["paymentMethod"]
            )

        # Map the shipping method.
        if transaction["data"].get("shipMethod"):
            transaction["data"]["shipMethod"] = self.ship_methods[
                transaction["data"]["shipMethod"]
            ]

        # Map country code.
        if transaction["data"].get("billingAddress"):
            transaction["data"]["billingAddress"]["country"] = self.countries[
                transaction["data"]["billingAddress"]["country"]
            ]

        if transaction["data"].get("shippingAddress"):
            transaction["data"]["shippingAddress"]["country"] = self.countries[
                transaction["data"]["shippingAddress"]["country"]
            ]

        return transaction

    def tx_transaction_tgt_ext(self, new_transaction, transaction):
        pass

    def insert_update_transactions(self, transactions):
        for transaction in transactions:
            tx_type = transaction.get("tx_type_src_id").split("-")[0]
            try:
                record_type = self.get_record_type(tx_type)
                assert (
                    record_type is not None
                ), f"{transaction['tx_type_src_id']}/{tx_type} is not supported."

                transaction["tgt_id"] = self.soap_connector.insert_update_transaction(
                    record_type, transaction["data"]
                )
                transaction["tx_status"] = "S"
            except Exception:
                log = traceback.format_exc()
                transaction.update({"tx_status": "F", "tx_note": log, "tgt_id": "####"})
                self.logger.exception(
                    f"Failed to create order: {transaction['tx_type_src_id']} with error: {log}"
                )
        return transactions

    def tx_person_tgt(self, person):
        tx_type = person.get("tx_type_src_id").split("-")[0]

        return person

    def tx_person_tgt_ext(self, new_person, person):
        pass

    def insert_update_persons(self, persons):
        for person in persons:
            tx_type = person.get("tx_type_src_id").split("-")[0]
            try:

                record_type = self.get_record_type(tx_type)
                assert record_type is not None, f"{tx_type} is not supported."

                person["tgt_id"] = self.soap_connector.insert_update_person(
                    record_type, person["data"]
                )
                person["tx_status"] = "S"
            except Exception:
                log = traceback.format_exc()
                person.update({"tx_status": "F", "tx_note": log, "tgt_id": "####"})
                self.logger.exception(
                    f"Failed to create order: {person['tx_type_src_id']} with error: {log}"
                )
        return persons
