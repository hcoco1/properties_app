import json
import boto3
import csv
import io
import os
from decimal import Decimal
import logging

logging.getLogger().setLevel(logging.INFO)

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # Log event for debugging
    logging.info(json.dumps(event))
    
    # Replace with your actual bucket and table names
    processed_bucket = os.environ['PROCESSED_BUCKET']
    table_name = os.environ['DYNAMODB_TABLE']

    # Extract S3 bucket and file details
    raw_bucket = event['Records'][0]['s3']['bucket']['name']
    csv_filename = event['Records'][0]['s3']['object']['key']
    
    # Log the bucket and filename being accessed
    logging.info(f"Fetching file: {csv_filename} from bucket: {raw_bucket}")
    
    try:
        obj = s3.get_object(Bucket=raw_bucket, Key=csv_filename)
    except s3.exceptions.NoSuchKey as e:
        logging.error(f"File {csv_filename} not found in bucket {raw_bucket}")
        raise e
    
    csv_data = obj['Body'].read().decode('utf-8').splitlines()
    
    processed_rows = []
    required_keys = ['zpid', 'streetAddress', 'unit', 'bedrooms', 
                     'bathrooms', 'homeType', 'priceChange', 'zipcode', 'city', 
                     'state', 'country', 'livingArea', 'taxAssessedValue', 
                     'priceReduction', 'datePriceChanged', 'homeStatus', 'price', 'currency']
    
    # Parsing CSV data
    reader = csv.DictReader(csv_data)
    for row in reader:
        filtered_row = {key: row[key] for key in required_keys if key in row}
        
        # Convert price if it exists and update the currency
        if 'price' in filtered_row and 'currency' in filtered_row:
            filtered_row['price'], filtered_row['currency'] = convert_currency(Decimal(filtered_row['price']), filtered_row['currency'])
        
        processed_rows.append(filtered_row)
    
    # Upload the processed data to DynamoDB and move the file to the processed bucket
    if processed_rows:
        upload_to_dynamodb(table_name, processed_rows)
        move_file_to_processed_bucket(raw_bucket, processed_bucket, csv_filename)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Currency Standardization complete!')
    }

# Bi-directional currency conversion (CAD to USD, USD to CAD)
def convert_currency(price, currency):
    # Define exchange rates (CAD to USD and USD to CAD)
    exchange_rates = {
        'CAD_to_USD': 0.75,
        'USD_to_CAD': 1.33,  # The reverse conversion rate
    }
    
    # Check if the currency is CAD and convert it to USD
    if currency == 'CAD':
        return price * Decimal(exchange_rates['CAD_to_USD']), 'USD'
    
    # Check if the currency is USD and convert it to CAD
    elif currency == 'USD':
        return price * Decimal(exchange_rates['USD_to_CAD']), 'CAD'
    
    # If no conversion is needed, return the original price and currency
    else:
        return price, currency


def upload_to_dynamodb(table_name, items):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    # Use batch writer to write multiple records at once
    with table.batch_writer() as batch:
        for item in items:
            # Convert all price-related fields to Decimal since DynamoDB expects it
            if 'price' in item:
                item['price'] = Decimal(item['price'])
            batch.put_item(Item=item)

def move_file_to_processed_bucket(raw_bucket_name, processed_bucket_name, file_key):
    s3 = boto3.resource('s3')
    copy_source = {
        'Bucket': raw_bucket_name,
        'Key': file_key
    }

    # Copy the file to the processed bucket
    s3.meta.client.copy(copy_source, processed_bucket_name, file_key)
    
    # Delete the original file from the raw bucket
    s3.Object(raw_bucket_name, file_key).delete()
