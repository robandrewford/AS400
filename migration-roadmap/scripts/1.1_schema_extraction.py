# scripts/1.1_schema_extraction.py
import pandas as pd
import hashlib

# Synthetic DB2/400 schema based on discovered applications
# Real implementation requires: DSPFD FILE(*ALL) OUTPUT(*OUTFILE) + SQL SYSTABLES query

schema_catalog = []

# WMS001 - Warehouse Management Core
schema_catalog.extend([
    {
        'App_ID': 'WMS001',
        'File_Name': 'WHITEM',
        'File_Type': 'PF',
        'Record_Format': 'WHITEMR',
        'Record_Length': 512,
        'Key_Fields': 'WAREHOUSE_ID,ITEM_SKU',
        'Record_Count': 45000000,
        'Columns': 'WAREHOUSE_ID CHAR(4), ITEM_SKU CHAR(14), QTY_ON_HAND INT, QTY_ALLOCATED INT, LOCATION_BIN CHAR(10), LAST_COUNT_DATE DATE, LAST_MOVEMENT_TS TIMESTAMP, COST_USD DECIMAL(15,4), WEIGHT_LBS DECIMAL(10,2), STATUS_CODE CHAR(1)',
        'Constraints': 'PK(WAREHOUSE_ID,ITEM_SKU), FK(ITEM_SKU)->INVMAST(ITEM_SKU), CHK(STATUS_CODE IN (A,H,D,X))',
        'LF_Count': 6,
        'Index_Strategy': 'Partition by WAREHOUSE_ID, cluster on ITEM_SKU'
    },
    {
        'App_ID': 'WMS001',
        'File_Name': 'WHLOC',
        'File_Type': 'PF',
        'Record_Format': 'WHLOCR',
        'Record_Length': 256,
        'Key_Fields': 'WAREHOUSE_ID,LOCATION_BIN',
        'Record_Count': 8500000,
        'Columns': 'WAREHOUSE_ID CHAR(4), LOCATION_BIN CHAR(10), ZONE_CODE CHAR(3), AISLE CHAR(3), BAY CHAR(3), LEVEL CHAR(2), CAPACITY_CUFT DECIMAL(10,2), OCCUPIED_CUFT DECIMAL(10,2), LOCK_STATUS CHAR(1), TEMP_CONTROL_FLG CHAR(1)',
        'Constraints': 'PK(WAREHOUSE_ID,LOCATION_BIN), CHK(LOCK_STATUS IN (U,L)), CHK(TEMP_CONTROL_FLG IN (Y,N))',
        'LF_Count': 4,
        'Index_Strategy': 'Partition by WAREHOUSE_ID, index on ZONE_CODE'
    },
    {
        'App_ID': 'WMS001',
        'File_Name': 'WHXFER',
        'File_Type': 'PF',
        'Record_Format': 'WHXFERR',
        'Record_Length': 384,
        'Key_Fields': 'XFER_ID',
        'Record_Count': 125000000,
        'Columns': 'XFER_ID INT, FROM_WAREHOUSE CHAR(4), TO_WAREHOUSE CHAR(4), ITEM_SKU CHAR(14), QTY_XFER INT, XFER_DATE DATE, SHIP_DATE DATE, RECV_DATE DATE, CARRIER_CODE CHAR(4), TRACKING_NUM CHAR(30), STATUS_CODE CHAR(1), CREATE_USER CHAR(10), CREATE_TS TIMESTAMP',
        'Constraints': 'PK(XFER_ID), FK(ITEM_SKU)->INVMAST(ITEM_SKU), FK(CARRIER_CODE)->CARRMAP(CARRIER_CODE), CHK(STATUS_CODE IN (P,S,T,R,C))',
        'LF_Count': 8,
        'Index_Strategy': 'Partition by XFER_DATE (monthly), index on FROM_WAREHOUSE, TO_WAREHOUSE'
    },
    {
        'App_ID': 'WMS001',
        'File_Name': 'WHADJ',
        'File_Type': 'PF',
        'Record_Format': 'WHADJR',
        'Record_Length': 320,
        'Key_Fields': 'ADJ_ID',
        'Record_Count': 38000000,
        'Columns': 'ADJ_ID INT, WAREHOUSE_ID CHAR(4), ITEM_SKU CHAR(14), ADJ_QTY INT, ADJ_REASON_CODE CHAR(3), ADJ_DATE DATE, CYCLE_COUNT_FLG CHAR(1), APPROVAL_USER CHAR(10), APPROVAL_TS TIMESTAMP, COST_IMPACT_USD DECIMAL(15,2), NOTES VARCHAR(500)',
        'Constraints': 'PK(ADJ_ID), FK(ITEM_SKU)->INVMAST(ITEM_SKU), CHK(CYCLE_COUNT_FLG IN (Y,N))',
        'LF_Count': 5,
        'Index_Strategy': 'Partition by ADJ_DATE (monthly), index on WAREHOUSE_ID, ADJ_REASON_CODE'
    }
])

# INV002 - Inventory Control System
schema_catalog.extend([
    {
        'App_ID': 'INV002',
        'File_Name': 'INVMAST',
        'File_Type': 'PF',
        'Record_Format': 'INVMASTR',
        'Record_Length': 1024,
        'Key_Fields': 'ITEM_SKU',
        'Record_Count': 12000000,
        'Columns': 'ITEM_SKU CHAR(14), ITEM_DESC VARCHAR(100), CATEGORY_CODE CHAR(6), SUBCATEGORY_CODE CHAR(6), VENDOR_ID INT, BRAND_NAME VARCHAR(50), UPC_CODE CHAR(12), COST_USD DECIMAL(15,4), RETAIL_USD DECIMAL(15,2), WEIGHT_LBS DECIMAL(10,2), LENGTH_IN DECIMAL(8,2), WIDTH_IN DECIMAL(8,2), HEIGHT_IN DECIMAL(8,2), HAZMAT_FLG CHAR(1), PERISHABLE_FLG CHAR(1), ACTIVE_FLG CHAR(1), CREATE_DATE DATE, LAST_MODIFIED_TS TIMESTAMP',
        'Constraints': 'PK(ITEM_SKU), FK(VENDOR_ID)->VENDMAST(VENDOR_ID), CHK(HAZMAT_FLG IN (Y,N)), CHK(PERISHABLE_FLG IN (Y,N)), CHK(ACTIVE_FLG IN (Y,N))',
        'LF_Count': 12,
        'Index_Strategy': 'Clustered on ITEM_SKU, indexes on CATEGORY_CODE, VENDOR_ID, UPC_CODE'
    },
    {
        'App_ID': 'INV002',
        'File_Name': 'INVTRAN',
        'File_Type': 'PF',
        'Record_Format': 'INVTRANR',
        'Record_Length': 448,
        'Key_Fields': 'TRAN_ID',
        'Record_Count': 850000000,
        'Columns': 'TRAN_ID BIGINT, ITEM_SKU CHAR(14), TRAN_TYPE_CODE CHAR(3), TRAN_DATE DATE, TRAN_TIME TIME, WAREHOUSE_ID CHAR(4), QTY_CHANGE INT, REFERENCE_DOC_ID VARCHAR(30), REFERENCE_DOC_TYPE CHAR(3), COST_IMPACT_USD DECIMAL(15,2), USER_ID CHAR(10), BATCH_ID INT',
        'Constraints': 'PK(TRAN_ID), FK(ITEM_SKU)->INVMAST(ITEM_SKU), CHK(TRAN_TYPE_CODE IN (RCV,SHP,ADJ,RTN,XFR,SAL,WRT))',
        'LF_Count': 10,
        'Index_Strategy': 'Partition by TRAN_DATE (daily, 90-day hot, rest archive), index on ITEM_SKU, WAREHOUSE_ID'
    },
    {
        'App_ID': 'INV002',
        'File_Name': 'INVBAL',
        'File_Type': 'LF',
        'Record_Format': 'INVBALR',
        'Record_Length': 256,
        'Key_Fields': 'ITEM_SKU,WAREHOUSE_ID',
        'Record_Count': 0,
        'Columns': 'SELECT ITEM_SKU, WAREHOUSE_ID, SUM(QTY_CHANGE) AS BALANCE_QTY FROM INVTRAN GROUP BY ITEM_SKU, WAREHOUSE_ID',
        'Constraints': 'LOGICAL VIEW over INVTRAN (materialized nightly for performance)',
        'LF_Count': 0,
        'Index_Strategy': 'Convert to BigQuery materialized view, refresh every 4 hours'
    },
    {
        'App_ID': 'INV002',
        'File_Name': 'INVAUDIT',
        'File_Type': 'PF',
        'Record_Format': 'INVAUDR',
        'Record_Length': 512,
        'Key_Fields': 'AUDIT_ID',
        'Record_Count': 420000000,
        'Columns': 'AUDIT_ID BIGINT, ITEM_SKU CHAR(14), FIELD_NAME CHAR(30), OLD_VALUE VARCHAR(200), NEW_VALUE VARCHAR(200), CHANGE_DATE DATE, CHANGE_TIME TIME, USER_ID CHAR(10), PROGRAM_NAME CHAR(10), JOB_NAME CHAR(28)',
        'Constraints': 'PK(AUDIT_ID), FK(ITEM_SKU)->INVMAST(ITEM_SKU)',
        'LF_Count': 3,
        'Index_Strategy': 'Partition by CHANGE_DATE (monthly), archive to Coldline after 2 years'
    }
])

# POS003 - Point of Sale Transaction
schema_catalog.extend([
    {
        'App_ID': 'POS003',
        'File_Name': 'POSSALE',
        'File_Type': 'PF',
        'Record_Format': 'POSSALER',
        'Record_Length': 640,
        'Key_Fields': 'SALE_ID',
        'Record_Count': 2800000000,
        'Columns': 'SALE_ID BIGINT, WAREHOUSE_ID CHAR(4), REGISTER_NUM CHAR(3), SALE_DATE DATE, SALE_TIME TIME, MEMBER_NUM INT, CASHIER_ID CHAR(10), SUBTOTAL_USD DECIMAL(15,2), TAX_USD DECIMAL(15,2), TOTAL_USD DECIMAL(15,2), TENDER_TYPE_CODE CHAR(2), CARD_LAST4 CHAR(4), CARD_TYPE CHAR(2), AUTH_CODE CHAR(10), RECEIPT_NUM CHAR(20), VOID_FLG CHAR(1), RETURN_FLG CHAR(1)',
        'Constraints': 'PK(SALE_ID), FK(MEMBER_NUM)->MBRMAST(MEMBER_NUM), CHK(TENDER_TYPE_CODE IN (CC,DC,CK,CS,GC)), CHK(VOID_FLG IN (Y,N)), CHK(RETURN_FLG IN (Y,N))',
        'LF_Count': 15,
        'Index_Strategy': 'Partition by SALE_DATE (daily), cluster on WAREHOUSE_ID, MEMBER_NUM'
    },
    {
        'App_ID': 'POS003',
        'File_Name': 'POSITEM',
        'File_Type': 'PF',
        'Record_Format': 'POSITEMR',
        'Record_Length': 384,
        'Key_Fields': 'SALE_ID,LINE_NUM',
        'Record_Count': 12500000000,
        'Columns': 'SALE_ID BIGINT, LINE_NUM SMALLINT, ITEM_SKU CHAR(14), QTY INT, UNIT_PRICE_USD DECIMAL(15,2), EXT_PRICE_USD DECIMAL(15,2), DISCOUNT_USD DECIMAL(15,2), PROMO_CODE CHAR(10), TAX_RATE DECIMAL(8,5), TAX_AMT_USD DECIMAL(15,2), COST_USD DECIMAL(15,4)',
        'Constraints': 'PK(SALE_ID,LINE_NUM), FK(SALE_ID)->POSSALE(SALE_ID), FK(ITEM_SKU)->INVMAST(ITEM_SKU), FK(PROMO_CODE)->PRCPROMO(PROMO_CODE)',
        'LF_Count': 8,
        'Index_Strategy': 'Partition by SALE_ID parent partition, index on ITEM_SKU'
    },
    {
        'App_ID': 'POS003',
        'File_Name': 'POSTENDR',
        'File_Type': 'PF',
        'Record_Format': 'POSTENDR',
        'Record_Length': 320,
        'Key_Fields': 'TENDER_ID',
        'Record_Count': 3200000000,
        'Columns': 'TENDER_ID BIGINT, SALE_ID BIGINT, TENDER_TYPE_CODE CHAR(2), TENDER_AMT_USD DECIMAL(15,2), CARD_TYPE CHAR(2), CARD_LAST4 CHAR(4), AUTH_CODE CHAR(10), GATEWAY_TRAN_ID VARCHAR(50), APPROVAL_TS TIMESTAMP, SETTLEMENT_DATE DATE, BATCH_NUM INT',
        'Constraints': 'PK(TENDER_ID), FK(SALE_ID)->POSSALE(SALE_ID)',
        'LF_Count': 6,
        'Index_Strategy': 'Partition by APPROVAL_TS (daily), index on SETTLEMENT_DATE for batch reconciliation'
    },
    {
        'App_ID': 'POS003',
        'File_Name': 'POSTAX',
        'File_Type': 'PF',
        'Record_Format': 'POSTAXR',
        'Record_Length': 256,
        'Key_Fields': 'SALE_ID,TAX_JURIS_CODE',
        'Record_Count': 3500000000,
        'Columns': 'SALE_ID BIGINT, TAX_JURIS_CODE CHAR(10), TAX_TYPE_CODE CHAR(3), TAXABLE_AMT_USD DECIMAL(15,2), TAX_RATE DECIMAL(8,5), TAX_AMT_USD DECIMAL(15,2), TAX_AUTHORITY VARCHAR(100)',
        'Constraints': 'PK(SALE_ID,TAX_JURIS_CODE), FK(SALE_ID)->POSSALE(SALE_ID), FK(TAX_JURIS_CODE)->TAXJURIS(TAX_JURIS_CODE)',
        'LF_Count': 4,
        'Index_Strategy': 'Partition by SALE_ID parent partition, index on TAX_JURIS_CODE'
    }
])

# PAYMENT007 - Payment Processing Gateway
schema_catalog.extend([
    {
        'App_ID': 'PAYMENT007',
        'File_Name': 'PYMTRAN',
        'File_Type': 'PF',
        'Record_FORMAT': 'PYMTRANR',
        'Record_Length': 768,
        'Key_Fields': 'TRAN_ID',
        'Record_Count': 4200000000,
        'Columns': 'TRAN_ID BIGINT, SALE_ID BIGINT, TRAN_TYPE_CODE CHAR(3), TRAN_DATE DATE, TRAN_TIME TIME, CARD_TYPE CHAR(2), CARD_TOKEN VARCHAR(64), CARD_LAST4 CHAR(4), EXP_MONTH CHAR(2), EXP_YEAR CHAR(4), AMOUNT_USD DECIMAL(15,2), CURRENCY_CODE CHAR(3), AUTH_CODE CHAR(10), GATEWAY_TRAN_ID VARCHAR(50), GATEWAY_NAME CHAR(20), RESPONSE_CODE CHAR(4), AVS_RESULT CHAR(1), CVV_RESULT CHAR(1), RISK_SCORE INT, PROCESSOR_FEE_USD DECIMAL(15,4), CREATE_TS TIMESTAMP',
        'Constraints': 'PK(TRAN_ID), FK(SALE_ID)->POSSALE(SALE_ID), CHK(TRAN_TYPE_CODE IN (AUT,CAP,VOI,REF)), CHK(CURRENCY_CODE=USD)',
        'LF_Count': 12,
        'Index_Strategy': 'Partition by TRAN_DATE (daily, 7-year retention for PCI), encrypt CARD_TOKEN with Cloud KMS'
    },
    {
        'App_ID': 'PAYMENT007',
        'File_Name': 'PYMAUTH',
        'File_Type': 'LF',
        'Record_Format': 'PYMAUTHR',
        'Record_Length': 384,
        'Key_Fields': 'TRAN_ID',
        'Record_Count': 0,
        'Columns': 'SELECT * FROM PYMTRAN WHERE TRAN_TYPE_CODE = AUT AND RESPONSE_CODE IN (0000,0001)',
        'Constraints': 'LOGICAL VIEW - approved authorizations only',
        'LF_Count': 0,
        'Index_Strategy': 'Convert to BigQuery view with row-level security (RLS)'
    },
    {
        'App_ID': 'PAYMENT007',
        'File_Name': 'PYMBATCH',
        'File_Type': 'PF',
        'Record_Format': 'PYMBATCHR',
        'Record_Length': 320,
        'Key_Fields': 'BATCH_ID',
        'Record_Count': 1200000,
        'Columns': 'BATCH_ID INT, BATCH_DATE DATE, SETTLEMENT_DATE DATE, BATCH_TYPE_CODE CHAR(3), GATEWAY_NAME CHAR(20), TRAN_COUNT INT, TOTAL_AMT_USD DECIMAL(15,2), STATUS_CODE CHAR(1), CLOSE_TS TIMESTAMP, RECONCILE_TS TIMESTAMP, GL_POST_DATE DATE',
        'Constraints': 'PK(BATCH_ID), CHK(BATCH_TYPE_CODE IN (SAL,REF)), CHK(STATUS_CODE IN (O,C,R,P))',
        'LF_Count': 3,
        'Index_Strategy': 'Index on BATCH_DATE, SETTLEMENT_DATE, GL_POST_DATE'
    },
    {
        'App_ID': 'PAYMENT007',
        'File_Name': 'PYMRECON',
        'File_Type': 'PF',
        'Record_Format': 'PYMRECONR',
        'Record_Length': 512,
        'Key_Fields': 'RECON_ID',
        'Record_Count': 850000,
        'Columns': 'RECON_ID INT, BATCH_ID INT, GATEWAY_NAME CHAR(20), GATEWAY_FILE_NAME VARCHAR(100), GATEWAY_TRAN_COUNT INT, GATEWAY_TOTAL_AMT_USD DECIMAL(15,2), SYSTEM_TRAN_COUNT INT, SYSTEM_TOTAL_AMT_USD DECIMAL(15,2), VARIANCE_AMT_USD DECIMAL(15,2), RECON_STATUS_CODE CHAR(1), RECON_DATE DATE, RECON_USER CHAR(10), NOTES VARCHAR(500)',
        'Constraints': 'PK(RECON_ID), FK(BATCH_ID)->PYMBATCH(BATCH_ID), CHK(RECON_STATUS_CODE IN (M,V,R))',
        'LF_Count': 2,
        'Index_Strategy': 'Index on BATCH_ID, RECON_DATE'
    }
])

# Convert to DataFrame for analysis
df_schema = pd.DataFrame(schema_catalog)

print("[DB2/400 SCHEMA CATALOG - SAMPLE (28 of 332 files)]")
print(df_schema[['App_ID', 'File_Name', 'File_Type', 'Record_Count', 'Record_Length']].to_markdown(index=False))

# Schema statistics
print(f"\n[SCHEMA STATISTICS]")
print(f"Total Physical Files Sampled: {len(df_schema[df_schema['File_Type'] == 'PF'])}")
print(f"Total Logical Files Sampled: {len(df_schema[df_schema['File_Type'] == 'LF'])}")
print(f"Total Record Count: {df_schema['Record_Count'].sum():,}")
print(f"Largest Table: {df_schema.nlargest(1, 'Record_Count')[['File_Name', 'Record_Count']].values[0]}")

# Calculate total data size
df_schema['Size_GB'] = (df_schema['Record_Count'] * df_schema['Record_Length']) / (1024**3)
total_size = df_schema['Size_GB'].sum()
print(f"Total Data Size (sampled): {total_size:,.2f} GB")

# Export DDL (synthetic PostgreSQL-compatible)
print("\n[SAMPLE DDL EXPORT - WHITEM table]")
print("""
CREATE TABLE warehouse_item (
    warehouse_id CHAR(4) NOT NULL,
    item_sku CHAR(14) NOT NULL,
    qty_on_hand INTEGER,
    qty_allocated INTEGER,
    location_bin CHAR(10),
    last_count_date DATE,
    last_movement_ts TIMESTAMP,
    cost_usd NUMERIC(15,4),
    weight_lbs NUMERIC(10,2),
    status_code CHAR(1),
    CONSTRAINT pk_warehouse_item PRIMARY KEY (warehouse_id, item_sku),
    CONSTRAINT fk_warehouse_item_invmast FOREIGN KEY (item_sku) REFERENCES inventory_master(item_sku),
    CONSTRAINT chk_warehouse_item_status CHECK (status_code IN ('A','H','D','X'))
)
PARTITION BY LIST (warehouse_id);
-- Note: BigQuery uses CLUSTER BY instead of partition for dimension tables
-- GCS staging: gs://costco-migration/schema/warehouse_item/*.parquet
""")

# Generate checksum
schema_csv = df_schema.to_csv(index=False)
checksum = hashlib.sha256(schema_csv.encode()).hexdigest()
print(f"\n[CHECKSUM: {checksum[:16]}]")