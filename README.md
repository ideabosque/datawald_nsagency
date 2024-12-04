# DataWald NSAgency Integration Guide

The `datawald_nsagency` module functions within the DataWald integration ecosystem, equipping it with `suitetalk_connector` capabilities for seamless data transformations. This module facilitates efficient data retrieval and insertion in NetSuite, ensuring a streamlined data flow across systems.

## Configuration Guide

To integrate `datawald_nsagency`, configure the necessary settings in the `se-configdata` table within DynamoDB, as detailed below.

### Core Configuration

Establish essential parameters for `datawald_nsagency` by adding these records:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "ACCOUNT",
    "value": "XXXXXXXXX"
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "CONSUMER_KEY",
    "value": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "CONSUMER_SECRET",
    "value": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "TOKEN_ID",
    "value": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "TOKEN_SECRET",
    "value": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

### SuiteTalk SOAP API Version Configuration

```json
{
  "setting_id": "datawald_nsagency",
  "variable": "VERSION",
  "value": "2023_1_0"
}
```

### Country Code Mapping

Standardize country identifiers across platforms:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "COUNTRIES",
    "value": {
        "AD": "_andorra",
        "AE": "_unitedArabEmirates",
        "AF": "_afghanistan",
        ...
    }
}
```

### Customer and Transaction Settings

Define policies and preferences for customer and transaction data handling:

- **Customer Creation Policy**: Specify if new customers should be created when not found in existing records.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "CREATE_CUSTOMER",
      "value": false
  }
  ```

- **Customer Deposit Creation**: List payment methods that require customer deposits.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "CREATE_CUSTOMER_DEPOSIT",
      "value": ["VISA", "Master Card"]
  }
  ```

- **Default Billing Address**: Choose whether to set the input billing address as the default.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "DEFAULT_TRANSACTION_BILLING",
      "value": true
  }
  ```

- **Page Limit**: Set a limit for the number of pages in search results.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "LIMIT_PAGES",
      "value": 10
  }
  ```

### Item and Transaction Mapping

Define mappings for item data and transaction details:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "NETSUITEMAPPINGS",
    "value": {
        "custom_records": {
            "customrecord_cseg_sales_class": "187",
            "customrecord_shipping_carrier": "164"
        },
        "inventory_detail_record_types": ["purchaseOrder", "itemReceipt", "itemFulfillment", "salesOrder", ...],
        "item_data_type": {
            "inventoryItem": "ns17:InventoryItem",
            "lotNumberedInventoryItem": "ns17:LotNumberedInventoryItem",
            "nonInventoryResaleItem": "ns17:NonInventoryResaleItem"
        },
        ...
    }
}
```

#### RESTful API Mapping

Map configurations for REST API interactions:

```json
{
 "setting_id": "datawald_nsagency",
 "variable": "NETSUITEMAPPINGSREST",
 "value": {
  "custom_records": {"customrecord_shipping_carrier": "164"},
  "item_data_type": {
   "inventoryItem": "ns17:InventoryItem",
   "lotNumberedInventoryItem": "ns17:LotNumberedInventoryItem",
   "nonInventoryResaleItem": "ns17:NonInventoryResaleItem"
  },
  "lookup_join_fields": {
   "invoice": {
    "base": ["invoice_tran_id|tranId", "invoice_status|status", "invoice_tran_date|tranDate", "invoice_total|total"],
    "created_from_types": ["salesOrder"],
    "lines": []
   },
   ...
 }
}
```

### Data Type Mapping

Establish the mappings between DataWald and NetSuite for data types:

```json
{
 "setting_id": "datawald_nsagency",
 "variable": "data_type",
 "value": {
  "billcredit": "vendorCredit",
  "company": "customer",
  "contact": "contact",
  "creditmemo": "creditMemo",
  ...
 }
}
```

### NetSuite Folder Internal ID

Specify the internal ID for processing files stored in NetSuite:

```json
{
 "setting_id": "datawald_nsagency",
 "variable": "ns_folder_internal_id",
 "value": "-10"
}
```

### Payment, Shipping, and Terms Mapping

Set mappings for payment, shipping, and term options:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "PAYMENT_METHODS",
    "value": {"####": "Wire", "authnetcim": "American Express", ...}
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "SHIP_METHODS",
    "value": {"####": "Truck", "ewp_ftl_shipping": "FTL Shipping", ...}
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "TERMS",
    "value": {"Cash": ["Cash"], ...}
}
```

### Timezone and Warehouse Settings

Define default timezone and specify active warehouse locations:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "TIMEZONE",
    "value": "America/Los_Angeles"
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "WAREHOUSES",
    "value": ["Los-Angeles", "New-York", ...]
}
```

### Source Metadata

Specify metadata structures for efficient data retrieval and synchronization:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "src_metadata",
    "value": {
        "billcredit": {
            "created_at": "createdDate",
            "src_id": "internalId",
            "updated_at": "lastModifiedDate"
        },
        ...
    }
}
```

### Data Transformation Mapping

Specify the column mappings and define transformation rules for data processing.

```json
{
  "datamart": {
    "customer": {
      "account_tags": {
        "funct": "','.join([i['name'] for i in src['account_tags']]) if src.get('account_tags') is not None else ''",
        "src": [
          {
            "key": "@custentityaccounts_tags",
            "label": "account_tags"
          }
        ],
        "type": "attribute"
      },
      "account_transfer_date": {
        "funct": "src['account_transfer_date'].astimezone(timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S') if src.get('account_transfer_date') is not None else ''",
        "src": [
          {
            "key": "@custentityaccount_transfer_date",
            "label": "account_transfer_date"
          }
        ],
        "type": "attribute"
      },
      "account_transfer_date_pst": {
        "funct": "src['account_transfer_date_pst'].strftime('%Y-%m-%d') if src.get('account_transfer_date_pst') is not None else ''",
        "src": [
          {
            "key": "@custentityaccount_transfer_date",
            "label": "account_transfer_date_pst"
          }
        ],
        "type": "attribute"
      },
      "annual_revenue": {
        "funct": "src.get('annual_revenue')",
        "src": [
          {
            "default": "",
            "key": "@custentity_annual_revenue",
            "label": "annual_revenue"
          }
        ],
        "type": "attribute"
      },
      "balance": {
        "funct": "src['balance'] if src.get('fe_customer_id') == '' else 0",
        "src": [
          {
            "default": "",
            "key": "balance",
            "label": "balance"
          }
        ],
        "type": "attribute"
      },
      "campaign_category": {
        "funct": "src.get('campaign_category')",
        "src": [
          {
            "default": "",
            "key": "campaignCategory|name",
            "label": "campaign_category"
          }
        ],
        "type": "attribute"
      },
      "category": {
        "funct": "src.get('category')",
        "src": [
          {
            "default": "",
            "key": "category|name",
            "label": "category"
          }
        ],
        "type": "attribute"
      },
      "company_name": {
        "funct": "src.get('company_name')",
        "src": [
          {
            "default": "",
            "key": "companyName",
            "label": "company_name"
          }
        ],
        "type": "attribute"
      },
      "contract_manufacturer": {
        "funct": "src.get('contract_manufacturer')",
        "src": [
          {
            "default": "",
            "key": "@custentity_contract_manufacturer",
            "label": "contract_manufacturer"
          }
        ],
        "type": "attribute"
      },
      "created_date": {
        "funct": "src['created_date'].astimezone(timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')",
        "src": [
          {
            "key": "dateCreated",
            "label": "created_date"
          }
        ],
        "type": "attribute"
      },
      "created_date_pst": {
        "funct": "src['created_date_pst'].strftime('%Y-%m-%d')",
        "src": [
          {
            "key": "dateCreated",
            "label": "created_date_pst"
          }
        ],
        "type": "attribute"
      },
      ...
    },
    "estimate": {
      "customer": {
        "funct": "src['customer']['name'] if src['customer'] is not None else ''",
        "src": [
          {
            "key": "entity",
            "label": "customer"
          }
        ],
        "type": "attribute"
      },
      "tran_id": {
        "funct": "src['tran_id']",
        "src": [
          {
            "key": "tranId",
            "label": "tran_id"
          }
        ],
        "type": "attribute"
      },
      "end_date": {
        "funct": "src['end_date'].astimezone(timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S') if src.get('end_date') else None",
        "src": [
          {
            "key": "endDate",
            "label": "end_date"
          }
        ],
        "type": "attribute"
      },
      ...
    },
    "inventory": {
      "locations": {
        "funct": {
          "full": {
            "funct": "src['full']",
            "src": [
              {
                "default": true,
                "label": "full"
              }
            ],
            "type": "attribute"
          },
          "in_stock": {
            "funct": "True if src.get('qty') is not None and src.get('qty') > 0 else False",
            "src": [
              {
                "key": "quantityAvailable",
                "label": "qty"
              }
            ],
            "type": "attribute"
          },
          ...
        },
        "src": [
          {
            "key": "locationsList|locations"
          }
        ],
        "type": "list"
      }
    },
    ...
  }
}
```

In this schema, each entry specifies the data transformation rules for different entities, including **customers**, **estimates**, **inventory**, and **invoices**. Each transformation consists of:
- `funct`: The function rule to apply for data manipulation, utilizing source data attributes.
- `src`: A list of source data attributes.
- `type`: Indicates the attribute type, e.g., `attribute` or `list`.

The JSON structure supports complex, nested mappings that facilitate flexible and accurate data transformations across various data categories.

### S3 Bucket and File Key Configuration

In cases where the `tx_map` exceeds the storage limits of a DynamoDB table cell, it will be stored in an S3 bucket. The configuration below specifies the S3 bucket and the file key path for the `txmap.json` file, ensuring easy retrieval and management.

#### Example Configuration:

```json
{
 "setting_id": "datawald_nsagency",
 "variable": "TXMAP_BUCKET",
 "value": "io-txmap-dev"  // S3 bucket for storing txmap.json
}
```

```json
{
 "setting_id": "datawald_nsagency",
 "variable": "TXMAP_KEY",
 "value": "ns/txmap.json"  // File key path for txmap.json in the S3 bucket
}
``` 

This setup enables efficient storage and access of large `tx_map` data in an S3 bucket using predefined identifiers.

This guide covers essential setup requirements for the `datawald_nsagency` integration, enabling a robust data management and interoperability framework across NetSuite and DataWald platforms.