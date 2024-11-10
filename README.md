# DataWald_nsagency Integration Guide

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

This guide covers essential setup requirements for the `datawald_nsagency` integration, enabling a robust data management and interoperability framework across NetSuite and DataWald platforms.