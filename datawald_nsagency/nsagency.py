#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import traceback, boto3, json, asyncio, time
import concurrent.futures
from datawald_agency import Agency
from datawald_connector import DatawaldConnector
from suitetalk_connector import SOAPConnector, RESTConnector
from datetime import datetime, timedelta
from pytz import timezone


class NSAgency(Agency):
    def __init__(self, logger, **setting):
        self.logger = logger
        self.setting = setting
        self.soap_connector = SOAPConnector(logger, **setting)
        self.rest_connector = RESTConnector(logger, **setting)
        self.datawald = DatawaldConnector(logger, **setting)
        Agency.__init__(self, logger, datawald=self.datawald)
        if setting.get("tx_type"):
            Agency.tx_type = setting.get("tx_type")

        if setting.get("TXMAP_BUCKET") and setting.get("TXMAP_KEY"):
            obj = self.s3(setting).get_object(
                Bucket=setting.get("TXMAP_BUCKET"), Key=setting.get("TXMAP_KEY")
            )
            self.map = json.loads(obj["Body"].read().decode("utf8"))
        else:
            self.map = setting.get("TXMAP", {})

        self.join = setting.get("JOIN", {"base": [], "lines": []})
        self.num_async_tasks = setting.get("NUM_ASYNC_TASKS", 10)

    def s3(self, setting):
        if (
            setting.get("region_name")
            and setting.get("aws_access_key_id")
            and setting.get("aws_secret_access_key")
        ):
            return boto3.client(
                "s3",
                region_name=setting.get("region_name"),
                aws_access_key_id=setting.get("aws_access_key_id"),
                aws_secret_access_key=setting.get("aws_secret_access_key"),
            )
        else:
            return boto3.client("s3")

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
        return self.setting["data_type"].get(tx_type)

    # Define your asynchronous function here (async_tx_entity_src)
    async def async_tx_entity_src(self, tx_entity_src, raw_entity, **kwargs):
        # Your asynchronous code here
        return tx_entity_src(raw_entity, **kwargs)

    ## We can move the decorator to the uplevel.
    def tx_entities_src_decorator():
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                try:
                    hours = float(kwargs.get("hours", 0.0))
                    cut_date = kwargs.get("cut_date").astimezone(
                        timezone(self.setting.get("TIMEZONE", "UTC"))
                    )
                    end_date = datetime.now(
                        tz=timezone(self.setting.get("TIMEZONE", "UTC"))
                    )

                    if hours > 0.0:
                        end_date = cut_date + timedelta(hours=hours)

                    kwargs = dict(
                        kwargs,
                        **{
                            "cut_date": cut_date.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        },
                    )

                    tx_entity_src, raw_entities = func(self, *args, **kwargs)

                    if kwargs.get("tx_type") == "product":
                        kwargs.update(
                            {"metadatas": self.get_product_metadatas(**kwargs)}
                        )

                    # Define a wrapper worker for the asynchronous task
                    async def task_wrapper(tx_entity_src, raw_entity, **kwargs):
                        return await self.async_tx_entity_src(
                            tx_entity_src, raw_entity, **kwargs
                        )

                    ## Create a pool of 10 processes
                    tasks = []
                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=50
                    ) as executor:
                        # Dispatch asynchronous tasks to different processes for raw_entity
                        for raw_entity in raw_entities:
                            tasks.append(
                                executor.submit(
                                    asyncio.run,
                                    task_wrapper(tx_entity_src, raw_entity, **kwargs),
                                )
                            )

                    # Track progress and calculate the percentage
                    total_tasks = len(tasks)
                    completed_tasks = 0

                    # Gather the tasks' results from the processes
                    entities = []
                    for task in concurrent.futures.as_completed(tasks):
                        result = task.result()
                        entities.append(result)
                        completed_tasks += 1
                        progress_percent = (completed_tasks / total_tasks) * 100
                        self.logger.info(
                            f"Progress (transferring {kwargs.get('tx_type')}): {progress_percent:.2f}%"
                        )

                    # entities = list(
                    #     map(
                    #         lambda raw_entity: tx_entity_src(raw_entity, **kwargs),
                    #         raw_entities,
                    #     )
                    # )
                    return entities
                except Exception:
                    self.logger.info(kwargs)
                    log = traceback.format_exc()
                    self.logger.exception(log)
                    raise

            return wrapper

        return decorator

    ## We can move the function to the uplevel.
    def tx_entity_src_decorator():
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                tx_type = kwargs.get("tx_type")

                self.logger.debug(
                    f"Transferring {tx_type} for {args[0]['internalId']} at {time.strftime('%X')}."
                )

                kwargs.update(
                    {
                        "entity": {
                            "src_id": args[0][
                                self.setting["src_metadata"][tx_type]["src_id"]
                            ],
                            "created_at": args[0][
                                self.setting["src_metadata"][tx_type]["created_at"]
                            ].astimezone(timezone("UTC")),
                            "updated_at": args[0][
                                self.setting["src_metadata"][tx_type]["updated_at"]
                            ].astimezone(timezone("UTC")),
                        }
                    }
                )

                entity = func(self, *args, **kwargs)
                return entity

            return wrapper

        return decorator

    ## We can move the function to the uplevel.
    def insert_update_decorator():
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                tx_type = args[0].get("tx_type_src_id").split("-")[0]
                try:
                    record_type = self.get_record_type(tx_type)
                    assert record_type is not None, f"{tx_type} is not supported."

                    kwargs.update({"record_type": record_type})
                    func(self, *args, **kwargs)
                except Exception:
                    log = traceback.format_exc()
                    args[0].update({"tx_status": "F", "tx_note": log, "tgt_id": "####"})
                    self.logger.exception(
                        f"Failed to create order: {args[0]['tx_type_src_id']} with error: {log}"
                    )

            return wrapper

        return decorator

    # Define your asynchronous function here (async_worker)
    async def async_worker(self, result_funct, record_type, **kwargs):
        # Your asynchronous code here
        return result_funct(record_type, **kwargs)

    def dispatch_async_worker(self, record_type, result_funct, limit_pages, **params):
        # Define a wrapper worker for the asynchronous task
        async def task_wrapper(result_funct, record_type, **kwargs):
            return await self.async_worker(result_funct, record_type, **kwargs)

        tasks = []
        # Create a multiprocessing Pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Dispatch asynchronous tasks to different processes for each page index
            for i in range(2, limit_pages + 1):
                tasks.append(
                    executor.submit(
                        asyncio.run,
                        task_wrapper(
                            result_funct,
                            record_type,
                            **dict(
                                params,
                                **{
                                    "page_index": i,
                                },
                            ),
                        ),
                    )
                )

        # Track progress and calculate the percentage
        total_tasks = len(tasks)
        completed_tasks = 0

        # Gather the tasks' results from the processes
        gathered_results = []
        for task in concurrent.futures.as_completed(tasks):
            result = task.result()
            gathered_results.append(result)
            completed_tasks += 1
            progress_percent = (completed_tasks / total_tasks) * 100
            self.logger.info(
                f"Progress (get_records_all for {record_type}): {progress_percent:.2f}%"
            )

        record_list = [entry["records"] for entry in gathered_results]
        records = [record for sublist in record_list for record in sublist]

        return records

    def get_records_all(self, record_type, result_funct, funct, **params):
        limit_pages = self.setting.get("LIMIT_PAGES", 3)
        result = result_funct(record_type, **params)
        if result["total_records"] == 0:
            return []

        if result["total_pages"] == 1:
            return funct(record_type, result["records"], **params)

        limit_pages = (
            result["total_pages"]
            if limit_pages == 0
            else min(limit_pages, result["total_pages"])
        )

        records = self.dispatch_async_worker(
            record_type,
            result_funct,
            limit_pages,
            **dict(params, **{"search_id": result["search_id"]}),
        )
        records = result["records"] + records

        return funct(record_type, records, **params)

    def get_records(self, record_type, result_funct, funct, **params):
        try:
            current_time = datetime.now(
                tz=timezone(self.setting.get("TIMEZONE", "UTC"))
            )
            hours = params.get("hours", 0.0)

            if hours == 0.0:
                end_time = current_time
            else:
                cut_date = params.get("cut_date")
                end_time = datetime.strptime(
                    cut_date, "%Y-%m-%dT%H:%M:%S%z"
                ) + timedelta(hours=hours)

            while True:
                self.logger.info(params)

                records = self.get_records_all(
                    record_type, result_funct, funct, **params
                )

                if len(records) >= 1 or end_time >= current_time:
                    return records

                end_time += timedelta(hours=hours)
                params.update({"end_date": end_time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        except Exception as e:
            log = traceback.format_exc()
            self.logger.exception(log)
            raise e

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

    ## We can move the function to the uplevel.
    @tx_entities_src_decorator()
    def tx_transactions_src(self, **kwargs):
        record_type = self.get_record_type(kwargs.get("tx_type"))
        assert record_type is not None, f"{kwargs.get('tx_type')} is not supported."

        raw_transactions = self.get_records(
            record_type,
            self.soap_connector.get_transaction_result,
            self.soap_connector.get_transactions,
            **kwargs,
        )

        return self.tx_transaction_src, raw_transactions

    ## We can move the function to the uplevel.
    @tx_entity_src_decorator()
    def tx_transaction_src(self, raw_transaction, **kwargs):
        tx_type = kwargs.get("tx_type")
        target = kwargs.get("target")
        transaction = kwargs.get("entity")
        try:
            transaction.update(
                {
                    "data": self.transform_data(
                        raw_transaction,
                        self.map[target].get(self.get_record_type(tx_type)),
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

    ## We can move the function to the uplevel.
    @tx_entities_src_decorator()
    def tx_assets_src(self, **kwargs):
        record_type = self.get_record_type(kwargs.get("tx_type"))
        assert record_type is not None, f"{kwargs.get('tx_type')} is not supported."

        raw_assets = self.get_records(
            record_type,
            self.soap_connector.get_item_result,
            self.soap_connector.get_items,
            **kwargs,
        )

        return self.tx_asset_src, raw_assets

    ## We can move the function to the uplevel.
    @tx_entity_src_decorator()
    def tx_asset_src(self, raw_asset, **kwargs):
        tx_type = kwargs.get("tx_type")
        target = kwargs.get("target")
        asset = kwargs.get("entity")
        try:
            if tx_type == "product":
                data = self.transform_data(raw_asset, kwargs.get("metadatas"))
            else:
                data = self.transform_data(
                    raw_asset, self.map[target].get(self.get_record_type(tx_type))
                )

            if tx_type == "inventory":
                inventory = data.get("locations")
                drop_ship_item = data.get("drop_ship_item", False)
                asset.update(
                    {
                        "data": {"inventory": inventory, "drop_ship_item": drop_ship_item},
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
            for location in inventory_number.get("locations", [])
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

    ## We can move the function to the uplevel.
    @tx_entities_src_decorator()
    def tx_persons_src(self, **kwargs):
        record_type = self.get_record_type(kwargs.get("tx_type"))
        assert record_type is not None, f"{kwargs.get('tx_type')} is not supported."

        raw_persons = self.get_records(
            record_type,
            self.soap_connector.get_person_result,
            self.soap_connector.get_persons,
            **kwargs,
        )

        return self.tx_person_src, raw_persons

    ## We can move the function to the uplevel.
    @tx_entity_src_decorator()
    def tx_person_src(self, raw_person, **kwargs):
        tx_type = kwargs.get("tx_type")
        target = kwargs.get("target")
        person = kwargs.get("entity")
        try:
            person.update(
                {"data": self.transform_data(raw_person, self.map[target].get(tx_type))}
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
            terms = self.get_term(transaction["data"]["paymentMethod"])
            if terms is not None:
                transaction["data"]["terms"] = terms

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
            self.insert_update_transaction(transaction)
        return transactions

    @insert_update_decorator()
    def insert_update_transaction(self, transaction, record_type=None):
        transaction["tgt_id"] = self.soap_connector.insert_update_transaction(
            record_type, transaction["data"]
        )
        transaction["tx_status"] = "S"

    def tx_person_tgt(self, person):
        tx_type = person.get("tx_type_src_id").split("-")[0]

        return person

    def tx_person_tgt_ext(self, new_person, person):
        pass

    def insert_update_persons(self, persons):
        for person in persons:
            self.insert_update_person(person)
        return persons

    @insert_update_decorator()
    def insert_update_person(self, person, record_type=None):
        person["tgt_id"] = self.soap_connector.insert_update_person(
            record_type, person["data"]
        )
        person["tx_status"] = "S"
