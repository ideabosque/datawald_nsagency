# datawald_nsagency Integration

The module operates within the DataWald integration framework, providing SuiteConnector capabilities to streamline data transformation processes. It enables seamless data retrieval from NetSuite as well as data insertion back into NetSuite, ensuring efficient data flow and integration.

## Configuration Guide

To integrate `datawald_nsagency`, you’ll need to populate the `se-configdata` table in DynamoDB with the necessary configuration settings as outlined below.

### Core Configuration

Add the following records to set up the foundational configuration for `datawald_nsagency`:

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

### Country Code Mapping

Define country codes to standardize identifiers across platforms:

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

Configure how customer data and transactions are handled:

- **Customer Creation Policy:** If no existing customer record is found, specify whether to create a new customer.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "CREATE_CUSTOMER",
      "value": false
  }
  ```

- **Customer Deposit Creation:** Specify payment methods that require customer deposits.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "CREATE_CUSTOMER_DEPOSIT",
      "value": [
          "VISA",
          "Master Card"
      ]
  }
  ```

- **Default Billing Address:** Set whether the input billing address should serve as the default.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "DEFAULT_TRANSACTION_BILLING",
      "value": true
  }
  ```

- **Page Limit:** Set the limit for pages displayed in search results.

  ```json
  {
      "setting_id": "datawald_nsagency",
      "variable": "LIMIT_PAGES",
      "value": 10
  }
  ```

### Item and Transaction Mapping

Establish mappings for handling item data and transaction details:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "NETSUITEMAPPINGS",
    "value": {
        "custom_records": {
            "customrecord_cseg_sales_class": "187",
            "customrecord_shipping_carrier": "164"
        },
        "inventory_detail_record_types": [
            "purchaseOrder",
            "itemReceipt",
            "itemFulfillment",
            "salesOrder",
            ...
        ],
        "item_data_type": {
            "inventoryItem": "ns17:InventoryItem",
            "lotNumberedInventoryItem": "ns17:LotNumberedInventoryItem",
            "nonInventoryResaleItem": "ns17:NonInventoryResaleItem"
        },
        ...
    }
}
```

### Payment, Shipping, and Terms Mapping

Configure mappings for payment methods, shipping options, and terms:

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "PAYMENT_METHODS",
    "value": {
        "####": "Wire",
        "authnetcim": "American Express",
        ...
    }
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "SHIP_METHODS",
    "value": {
        "####": "Truck",
        "ewp_ftl_shipping": "FTL Shipping",
        ...
    }
}
```

```json
{
    "setting_id": "datawald_nsagency",
    "variable": "TERMS",
    "value": {
        "Cash": ["Cash"],
        ...
    }
}
```

### Timezone and Warehouse Settings

Set the default timezone and active warehouses:

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
    "value": [
        "Los-Angeles",
        "New-York",
        ...
    ]
}
```

### Source Metadata

Define metadata structure for source records to facilitate data retrieval and synchronization:

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

This configuration guide outlines the required setup for integrating `datawald_nsagency` effectively, covering essential parameters to optimize data management and interoperability.