# scripts/2.2_api_extraction_analysis.py
import pandas as pd

# Synthetic RPG/COBOL program analysis (real implementation requires source code parsing)

api_candidates = []

# POS003 - Price Lookup (CRITICAL priority)
api_candidates.append({
    'App_ID': 'POS003',
    'Program_Name': 'PRICE013/PRCLOOKUPR',
    'Language': 'RPG_IV',
    'SLOC': 2400,
    'Entry_Point': 'EXPORT PROCEDURE PRCLOOKUPR',
    'Parameters': 'INPUT: ITEM_SKU CHAR(14), WAREHOUSE_ID CHAR(4); OUTPUT: PRICE_USD PACKED(15,2), PROMO_CODE CHAR(10), EFFECTIVE_DATE DATE',
    'Business_Logic': 'Check PRCMAST for base price → Check PRCPROMO for active promotions → Apply warehouse-specific overrides → Return effective price',
    'DB_Operations': 'SELECT from PRCMAST, PRCPROMO (indexed reads)',
    'External_Calls': 'None',
    'Complexity_Score': 3.2,
    'API_Viability': 'HIGH',
    'Proposed_API_Endpoint': 'GET /api/v1/pricing/{item_sku}?warehouse_id={warehouse_id}',
    'Response_Format': '{"item_sku": "...", "price_usd": 99.99, "promo_code": "BF2025", "effective_date": "2025-11-15"}',
    'Cache_Strategy': 'Memorystore (Redis), 15-minute TTL',
    'Migration_Approach': 'Strangler Fig: Deploy Cloud Run API, gradually redirect POS terminals',
    'Estimated_Effort_Days': 15
})

# WMS001 - Inventory Balance Lookup
api_candidates.append({
    'App_ID': 'WMS001',
    'Program_Name': 'INV002/INVBALR',
    'Language': 'COBOL_400',
    'SLOC': 1800,
    'Entry_Point': 'IDENTIFICATION DIVISION. PROGRAM-ID. INVBALR.',
    'Parameters': 'INPUT: ITEM-SKU PIC X(14), WAREHOUSE-ID PIC X(4); OUTPUT: QTY-ON-HAND PIC S9(9), QTY-ALLOCATED PIC S9(9), QTY-AVAILABLE PIC S9(9)',
    'Business_Logic': 'Read WHITEM for QTY_ON_HAND, QTY_ALLOCATED → Calculate QTY_AVAILABLE = QTY_ON_HAND - QTY_ALLOCATED → Check for pending transfers in WHXFER',
    'DB_Operations': 'SELECT from WHITEM (PK read), SUM from WHXFER WHERE STATUS=P',
    'External_Calls': 'None',
    'Complexity_Score': 2.8,
    'API_Viability': 'HIGH',
    'Proposed_API_Endpoint': 'GET /api/v1/inventory/balance/{item_sku}?warehouse_id={warehouse_id}',
    'Response_Format': '{"item_sku": "...", "warehouse_id": "...", "qty_on_hand": 5000, "qty_allocated": 1200, "qty_available": 3800}',
    'Cache_Strategy': 'BigQuery cached view (4-hour refresh), Memorystore for hot items',
    'Migration_Approach': 'Replace AS400 Data Queue with Pub/Sub + Cloud Run API',
    'Estimated_Effort_Days': 12
})

# MEMBER006 - Member Lookup
api_candidates.append({
    'App_ID': 'MEMBER006',
    'Program_Name': 'MEMBER006/MBRLOOKUP',
    'Language': 'RPG_IV',
    'SLOC': 3200,
    'Entry_Point': 'EXPORT PROCEDURE MBRLOOKUP',
    'Parameters': 'INPUT: MEMBER_NUM PACKED(10,0) OR EMAIL CHAR(100); OUTPUT: MEMBER_RECORD (struct with 45 fields)',
    'Business_Logic': 'Lookup MBRMAST by MEMBER_NUM or EMAIL → Join MBRADDR for address → Check MBRHIST for renewal status → Return enriched member record',
    'DB_Operations': 'SELECT from MBRMAST (PK or email index), JOIN MBRADDR, LEFT JOIN MBRHIST',
    'External_Calls': 'None',
    'Complexity_Score': 4.1,
    'API_Viability': 'MEDIUM',
    'Proposed_API_Endpoint': 'GET /api/v1/members/{member_num} OR POST /api/v1/members/search (for email lookup)',
    'Response_Format': '{"member_num": 12345678, "name": {...}, "address": {...}, "membership": {...}, "privacy": {...}}',
    'Cache_Strategy': 'Cloud SQL read replica, DLP API for PII masking',
    'Migration_Approach': 'Dual-write during transition, cutover after validation',
    'Estimated_Effort_Days': 20
})

# PAYMENT007 - Authorization Check
api_candidates.append({
    'App_ID': 'PAYMENT007',
    'Program_Name': 'PAYMENT007/AUTHCHECK',
    'Language': 'RPG_IV',
    'SLOC': 4800,
    'Entry_Point': 'EXPORT PROCEDURE AUTHCHECK',
    'Parameters': 'INPUT: CARD_TOKEN CHAR(64), AMOUNT_USD PACKED(15,2), MERCHANT_ID CHAR(20); OUTPUT: AUTH_RESULT (struct), AUTH_CODE CHAR(10), RISK_SCORE INT',
    'Business_Logic': 'Call external payment gateway → Parse response → Check fraud rules → Log transaction to PYMTRAN → Return auth result',
    'DB_Operations': 'INSERT into PYMTRAN, SELECT from PYMAUTH for duplicate check',
    'External_Calls': 'Visa/MC Payment Gateway (HTTPS/REST)',
    'Complexity_Score': 6.7,
    'API_Viability': 'LOW',
    'Proposed_API_Endpoint': 'N/A - keep as Cloud Run service (not public API)',
    'Response_Format': 'Internal service only',
    'Cache_Strategy': 'None (PCI compliance - no caching of auth data)',
    'Migration_Approach': 'Rewrite in Python, deploy to Cloud Run with Cloud Armor WAF',
    'Estimated_Effort_Days': 35
})

# SHIP004 - Carrier Rate Calculation
api_candidates.append({
    'App_ID': 'SHIP004',
    'Program_Name': 'SHIP004/RATECALC',
    'Language': 'CL',
    'SLOC': 1200,
    'Entry_Point': 'PGM RATECALC',
    'Parameters': 'INPUT: FROM_ZIP CHAR(5), TO_ZIP CHAR(5), WEIGHT_LBS PACKED(10,2), SERVICE_LEVEL CHAR(3); OUTPUT: RATE_USD PACKED(15,2), CARRIER_CODE CHAR(4)',
    'Business_Logic': 'Lookup CARRRATE by zone (FROM_ZIP→TO_ZIP mapping) → Apply weight-based tier → Check for service-level surcharges → Return lowest-cost carrier',
    'DB_Operations': 'SELECT from CARRRATE (composite index on FROM_ZONE, TO_ZONE, WEIGHT_TIER)',
    'External_Calls': 'Optional: Call UPS/FedEx API for real-time rate (if CARRRATE cache stale)',
    'Complexity_Score': 3.5,
    'API_Viability': 'HIGH',
    'Proposed_API_Endpoint': 'POST /api/v1/shipping/rate-quote',
    'Response_Format': '{"from_zip": "...", "to_zip": "...", "weight_lbs": 25.5, "service_level": "GRD", "rate_usd": 18.75, "carrier": "UPS"}',
    'Cache_Strategy': 'Memorystore (Redis), daily refresh from carrier APIs',
    'Migration_Approach': 'Cloud Run API, parallel run with CL for validation',
    'Estimated_Effort_Days': 10
})

# TAX012 - Tax Calculation
api_candidates.append({
    'App_ID': 'TAX012',
    'Program_Name': 'TAX012/TAXCALC',
    'Language': 'COBOL_400',
    'SLOC': 3600,
    'Entry_Point': 'IDENTIFICATION DIVISION. PROGRAM-ID. TAXCALC.',
    'Parameters': 'INPUT: SALE-ITEMS-ARRAY (up to 50 items), SHIP-TO-ZIP PIC X(10); OUTPUT: TAX-DETAILS-ARRAY (by jurisdiction)',
    'Business_Logic': 'For each item: Determine tax category → Lookup TAXJURIS by ZIP → Apply TAXRATE (state, county, city, special district) → Check TAXEXCEPT for exemptions → Return tax breakdown',
    'DB_Operations': 'SELECT from TAXJURIS (ZIP index), SELECT from TAXRATE (jurisdiction + category), LEFT JOIN TAXEXCEPT',
    'External_Calls': 'TaxJar API (fallback if local data stale)',
    'Complexity_Score': 5.4,
    'API_Viability': 'MEDIUM',
    'Proposed_API_Endpoint': 'POST /api/v1/tax/calculate',
    'Response_Format': '[{"jurisdiction": "CA-State", "tax_rate": 0.0725, "taxable_amount": 100.00, "tax_amount": 7.25}, {...}]',
    'Cache_Strategy': 'Memorystore (Redis) for TAXRATE table, 24-hour TTL',
    'Migration_Approach': 'Cloud Run API with Cloud SQL replica, TaxJar as fallback',
    'Estimated_Effort_Days': 18
})

# ALLOCATION025 - Warehouse Allocation Engine
api_candidates.append({
    'App_ID': 'ALLOCATION025',
    'Program_Name': 'ALLOCATION025/ALLOCEXEC',
    'Language': 'COBOL_400',
    'SLOC': 7800,
    'Entry_Point': 'IDENTIFICATION DIVISION. PROGRAM-ID. ALLOCEXEC.',
    'Parameters': 'INPUT: ITEM-SKU PIC X(14), REQUIRED-QTY PIC S9(9); OUTPUT: ALLOCATION-PLAN (array of warehouse allocations)',
    'Business_Logic': 'Query WHITEM for all warehouses → Apply ALLOCRULE (priority, capacity, distance) → Calculate optimal allocation → Reserve QTY_ALLOCATED → Return allocation plan',
    'DB_Operations': 'SELECT from WHITEM (all warehouses for SKU), SELECT from ALLOCRULE, UPDATE WHITEM.QTY_ALLOCATED',
    'External_Calls': 'None',
    'Complexity_Score': 7.9,
    'API_Viability': 'LOW',
    'Proposed_API_Endpoint': 'N/A - batch job, not API candidate',
    'Response_Format': 'N/A',
    'Cache_Strategy': 'N/A',
    'Migration_Approach': 'Rewrite as Cloud Composer DAG (Airflow) + Dataflow for allocation logic',
    'Estimated_Effort_Days': 45
})

# LOYALTY021 - Points Accrual
api_candidates.append({
    'App_ID': 'LOYALTY021',
    'Program_Name': 'LOYALTY021/PTSACCRUE',
    'Language': 'RPG_IV',
    'SLOC': 2800,
    'Entry_Point': 'EXPORT PROCEDURE PTSACCRUE',
    'Parameters': 'INPUT: MEMBER_NUM PACKED(10,0), SALE_ID BIGINT, TOTAL_USD PACKED(15,2); OUTPUT: POINTS_EARNED INT, NEW_BALANCE INT',
    'Business_Logic': 'Lookup LOYALPTS for current balance → Apply earning rules (1 point per $1, bonus for tiers) → Check LOYALREWD for active bonuses → Update LOYALPTS → Return points earned',
    'DB_Operations': 'SELECT from LOYALPTS (PK read), SELECT from LOYALREWD, UPDATE LOYALPTS',
    'External_Calls': 'None',
    'Complexity_Score': 4.2,
    'API_Viability': 'HIGH',
    'Proposed_API_Endpoint': 'POST /api/v1/loyalty/accrue',
    'Response_Format': '{"member_num": 12345678, "sale_id": 987654321, "points_earned": 125, "new_balance": 8475}',
    'Cache_Strategy': 'Cloud SQL with read replicas, eventually consistent',
    'Migration_Approach': 'Pub/Sub subscriber → Cloud Run async handler',
    'Estimated_Effort_Days': 14
})

df_api_candidates = pd.DataFrame(api_candidates)

print("[API EXTRACTION CANDIDATES]")
print(df_api_candidates[['App_ID', 'Program_Name', 'Language', 'SLOC', 'API_Viability', 'Estimated_Effort_Days']].to_markdown(index=False))

print("\n[HIGH-VIABILITY API CANDIDATES (Priority for Cloud Run migration)]")
high_viability = df_api_candidates[df_api_candidates['API_Viability'] == 'HIGH'].sort_values('Estimated_Effort_Days')
print(high_viability[['Program_Name', 'Proposed_API_Endpoint', 'Cache_Strategy', 'Estimated_Effort_Days']].to_markdown(index=False))

# Generate OpenAPI 3.0 spec for top candidate (Price Lookup)
print("\n[OPENAPI 3.0 SPECIFICATION - Price Lookup API]")
print("""
openapi: 3.0.3
info:
  title: Costco Pricing API
  description: Real-time price lookup with promotion and warehouse-specific overrides
  version: 1.0.0
  contact:
    name: API Support
    email: api-support@costco.com

servers:
  - url: https://api.costco.com/v1
    description: Production
  - url: https://api-staging.costco.com/v1
    description: Staging

paths:
  /pricing/{item_sku}:
    get:
      summary: Get effective price for an item
      operationId: getPricing
      tags:
        - Pricing
      parameters:
        - name: item_sku
          in: path
          required: true
          schema:
            type: string
            pattern: '^[A-Z0-9]{14}$'
          description: 14-character item SKU
        - name: warehouse_id
          in: query
          required: true
          schema:
            type: string
            pattern: '^W[0-9]{3}$'
          description: 4-character warehouse ID (e.g., W001)
        - name: member_num
          in: query
          required: false
          schema:
            type: integer
          description: Member number for tier-based pricing (optional)
      responses:
        '200':
          description: Successful price lookup
          content:
            application/json:
              schema:
                type: object
                properties:
                  item_sku:
                    type: string
                  warehouse_id:
                    type: string
                  price_usd:
                    type: number
                    format: decimal
                  promo_code:
                    type: string
                    nullable: true
                  promo_price_usd:
                    type: number
                    format: decimal
                    nullable: true
                  effective_date:
                    type: string
                    format: date
                  member_only:
                    type: boolean
        '404':
          description: Item not found or not available in warehouse
        '429':
          description: Rate limit exceeded (1000 req/min per API key)
        '500':
          description: Internal server error
      security:
        - ApiKeyAuth: []

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for authentication (obtain from API Gateway)
""")

print("\n[TOTAL ESTIMATED EFFORT]")
total_effort = df_api_candidates['Estimated_Effort_Days'].sum()
print(f"API Extraction: {total_effort} developer-days (~{total_effort/20:.1f} developer-months)")
print(f"Assuming 2-person team: ~{total_effort/40:.1f} calendar months for all 8 candidates")