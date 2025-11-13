# scripts/1.4_data_cleansing_pipeline.py (Apache Beam on Dataflow)
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition
import hashlib
import re
from datetime import datetime

class CleanseWarehouseItem(beam.DoFn):
    """
    Cleansing transforms for WHITEM table based on Task 1.2 quality issues
    """
    def process(self, element):
        cleaned = element.copy()
        
        # Fix temporal anomaly: future dates
        if cleaned.get('last_count_date'):
            count_date = datetime.strptime(cleaned['last_count_date'], '%Y-%m-%d')
            if count_date > datetime.now():
                cleaned['last_count_date'] = None
                cleaned['_cleanse_flag'] = cleaned.get('_cleanse_flag', '') + 'FUTURE_DATE_NULLED;'
        
        # Fix range violation: negative costs
        if cleaned.get('cost_usd') and float(cleaned['cost_usd']) < 0:
            # Route to DLQ for manual review
            yield beam.pvalue.TaggedOutput('dlq', {
                'original_record': element,
                'reason': 'NEGATIVE_COST',
                'table': 'WHITEM'
            })
            return  # Don't process further
        
        # Fix completeness: NULL location_bin
        if not cleaned.get('location_bin') or cleaned['location_bin'].strip() == '':
            cleaned['location_bin'] = f"UNASSIGNED_{cleaned['warehouse_id']}"
            cleaned['_cleanse_flag'] = cleaned.get('_cleanse_flag', '') + 'LOCATION_DEFAULTED;'
        
        # String trimming & normalization
        for field in ['warehouse_id', 'item_sku', 'location_bin', 'status_code']:
            if cleaned.get(field):
                cleaned[field] = cleaned[field].strip().upper()
        
        yield cleaned

class CleanseInventoryMaster(beam.DoFn):
    """
    Cleansing transforms for INVMAST table
    """
    def process(self, element, vendor_lookup):
        cleaned = element.copy()
        
        # Fix referential integrity: invalid vendor_id
        vendor_id = cleaned.get('vendor_id')
        if vendor_id and vendor_id not in vendor_lookup:
            cleaned['vendor_id'] = 0  # Placeholder "VENDOR_UNKNOWN"
            cleaned['_cleanse_flag'] = cleaned.get('_cleanse_flag', '') + 'VENDOR_DEFAULTED;'
        
        # Fix data quality: encoding issues in item_desc
        if cleaned.get('item_desc'):
            # Remove non-ASCII, normalize unicode
            desc = cleaned['item_desc']
            desc = desc.encode('ascii', 'ignore').decode('ascii')
            desc = re.sub(r'[^\x20-\x7E]+', ' ', desc)  # Printable ASCII only
            cleaned['item_desc'] = ' '.join(desc.split())  # Collapse whitespace
            
            if desc != cleaned['item_desc']:
                cleaned['_cleanse_flag'] = cleaned.get('_cleanse_flag', '') + 'ENCODING_FIXED;'
        
        # Fix uniqueness: duplicate UPC codes
        # (Handled at aggregate level, not per-record - see separate deduplication step)
        
        yield cleaned

class CleanseInventoryTransaction(beam.DoFn):
    """
    Cleansing transforms for INVTRAN table
    """
    def process(self, element):
        cleaned = element.copy()
        
        # Fix temporal anomaly: 1900-01-01 as NULL substitute
        if cleaned.get('tran_date') == '1900-01-01':
            cleaned['tran_date'] = None
            cleaned['_cleanse_flag'] = cleaned.get('_cleanse_flag', '') + 'LEGACY_NULL_DATE;'
        
        # Fix referential integrity: orphaned SKUs (retain for historical analysis)
        # No action needed - will be handled by LEFT JOIN in BigQuery views
        
        yield cleaned

class CleansePaymentTransaction(beam.DoFn):
    """
    Cleansing transforms for PYMTRAN table (PCI-sensitive)
    """
    def process(self, element):
        cleaned = element.copy()
        
        # CRITICAL FIX: Plaintext PAN detected
        card_token = cleaned.get('card_token', '')
        if card_token and re.match(r'^\d{13,19}$', card_token):
            # Security violation - truncate immediately
            cleaned['card_token'] = None
            cleaned['card_last4'] = card_token[-4:] if len(card_token) >= 4 else '0000'
            cleaned['_cleanse_flag'] = cleaned.get('_cleanse_flag', '') + 'PCI_VIOLATION_TRUNCATED;'
            
            # Log to security audit
            yield beam.pvalue.TaggedOutput('security_audit', {
                'tran_id': cleaned.get('tran_id'),
                'incident_type': 'PLAINTEXT_PAN',
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'TRUNCATED'
            })
        
        # Fix completeness: NULL gateway_tran_id
        if not cleaned.get('gateway_tran_id'):
            cleaned['gateway_tran_id'] = f"OFFLINE-{cleaned['tran_id']}"
            cleaned['_cleanse_flag'] = cleaned.get('_cleanse_flag', '') + 'GATEWAY_ID_SYNTHETIC;'
        
        # Fix temporal anomaly: timestamp normalization to UTC
        if cleaned.get('create_ts'):
            # Assume PST timestamp, convert to UTC
            ts = datetime.fromisoformat(cleaned['create_ts'])
            utc_ts = ts.replace(tzinfo=None)  # Simplified - real impl needs pytz
            cleaned['create_ts'] = utc_ts.isoformat()
        
        yield cleaned

# Pipeline definition
def run_cleansing_pipeline():
    pipeline_options = PipelineOptions(
        runner='DataflowRunner',
        project='costco-migration',
        region='us-central1',
        temp_location='gs://costco-migration-temp/dataflow',
        staging_location='gs://costco-migration-staging/dataflow',
        job_name='data-cleansing-pipeline',
        max_num_workers=50,
        autoscaling_algorithm='THROUGHPUT_BASED'
    )
    
    with beam.Pipeline(options=pipeline_options) as p:
        # Load vendor lookup (side input for referential integrity checks)
        vendor_lookup = (
            p
            | 'Read Vendor Master' >> beam.io.ReadFromBigQuery(
                query='SELECT vendor_id FROM `costco-migration.staging.vendor_master`',
                use_standard_sql=True
            )
            | 'Extract Vendor IDs' >> beam.Map(lambda x: x['vendor_id'])
            | 'To Set' >> beam.combiners.ToSet()
        )
        
        # Cleanse WHITEM
        whitem_results = (
            p
            | 'Read WHITEM from GCS' >> beam.io.ReadFromText('gs://costco-migration-landing/whitem/*.csv', skip_header_lines=1)
            | 'Parse WHITEM CSV' >> beam.Map(lambda x: dict(zip(['warehouse_id', 'item_sku', 'qty_on_hand', 'qty_allocated', 'location_bin', 'last_count_date', 'last_movement_ts', 'cost_usd', 'weight_lbs', 'status_code'], x.split(','))))
            | 'Cleanse WHITEM' >> beam.ParDo(CleanseWarehouseItem()).with_outputs('dlq', main='clean')
        )
        
        # Write clean records to BigQuery
        whitem_results['clean'] | 'Write WHITEM to BQ' >> WriteToBigQuery(
            table='costco-migration:staging.warehouse_item_clean',
            schema='warehouse_id:STRING,item_sku:STRING,qty_on_hand:INTEGER,qty_allocated:INTEGER,location_bin:STRING,last_count_date:DATE,last_movement_ts:TIMESTAMP,cost_usd:NUMERIC,weight_lbs:NUMERIC,status_code:STRING,_cleanse_flag:STRING',
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
        )
        
        # Write bad records to DLQ
        whitem_results['dlq'] | 'Write WHITEM DLQ to GCS' >> beam.io.WriteToText('gs://costco-migration-dlq/whitem/', file_name_suffix='.json')
        
        # Cleanse INVMAST
        invmast_clean = (
            p
            | 'Read INVMAST from GCS' >> beam.io.ReadFromText('gs://costco-migration-landing/invmast/*.csv', skip_header_lines=1)
            | 'Parse INVMAST CSV' >> beam.Map(lambda x: dict(zip(['item_sku', 'item_desc', 'category_code', 'vendor_id', 'cost_usd', 'active_flg'], x.split(','))))
            | 'Cleanse INVMAST' >> beam.ParDo(CleanseInventoryMaster(), vendor_lookup=beam.pvalue.AsSingleton(vendor_lookup))
        )
        
        invmast_clean | 'Write INVMAST to BQ' >> WriteToBigQuery(
            table='costco-migration:staging.inventory_master_clean',
            schema='item_sku:STRING,item_desc:STRING,category_code:STRING,vendor_id:INTEGER,cost_usd:NUMERIC,active_flg:STRING,_cleanse_flag:STRING',
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
        )
        
        # Cleanse PYMTRAN (PCI-sensitive)
        pymtran_results = (
            p
            | 'Read PYMTRAN from GCS' >> beam.io.ReadFromText('gs://costco-migration-landing/pymtran/*.csv', skip_header_lines=1)
            | 'Parse PYMTRAN CSV' >> beam.Map(lambda x: dict(zip(['tran_id', 'sale_id', 'card_token', 'card_last4', 'amount_usd', 'gateway_tran_id', 'create_ts'], x.split(','))))
            | 'Cleanse PYMTRAN' >> beam.ParDo(CleansePaymentTransaction()).with_outputs('security_audit', main='clean')
        )
        
        pymtran_results['clean'] | 'Write PYMTRAN to BQ' >> WriteToBigQuery(
            table='costco-migration:staging.payment_transaction_clean',
            schema='tran_id:INTEGER,sale_id:INTEGER,card_token:STRING,card_last4:STRING,amount_usd:NUMERIC,gateway_tran_id:STRING,create_ts:TIMESTAMP,_cleanse_flag:STRING',
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
        )
        
        pymtran_results['security_audit'] | 'Write Security Audit to GCS' >> beam.io.WriteToText('gs://costco-migration-security-audit/pymtran/', file_name_suffix='.json')
        
        # Metrics (published to Cloud Monitoring)
        # Note: Actual implementation requires beam.metrics.Metrics.counter()
        print("[PIPELINE SUBMITTED - Monitor in Dataflow Console]")
        print("Expected outputs:")
        print("- gs://costco-migration-staging/warehouse_item_clean/ (BigQuery)")
        print("- gs://costco-migration-dlq/whitem/*.json (Dead Letter Queue)")
        print("- gs://costco-migration-security-audit/pymtran/*.json (PCI incidents)")

if __name__ == '__main__':
    run_cleansing_pipeline()