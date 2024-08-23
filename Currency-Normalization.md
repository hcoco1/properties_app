# Python for the Cloud Capstone Project: Currency Standardization

## Overview and Objectives

**Project Overview:**

Welcome to the Currency Standardization Capstone Project. In this project, you will build a solution that automates the process of standardizing financial data across different currencies. Upon completion, 
you will have a cloud-based application capable of converting property sale prices between CAD and USD and storing the transaction records efficiently.

**Learning Objectives:**

- Apply Python programming for data manipulation.
- Understand and implement Lambda functions for processing data.
- Utilize S3 for handling raw and processed data.
- Employ DynamoDB to store and retrieve processed information.


## The Task

You are tasked with developing a cloud-based system that standardizes data from property sales records, converting prices from CAD to USD. 
The system should store the results in a DynamoDB table and save the processed CSV records in a secondary S3 bucket.

**Architecture Overview:**

The system will consist of:

* **Two S3 buckets:** One for raw data and another for processed data.
* **Lambda Function:** For automating the processing of data files.
* **DynamoDB Table:** To store processed financial records.
* **AWS CDK:** For initial setup and deployment of AWS resources.


## Documentation

It is highly recomended that you document your journey through this exercise. The deployed application serves as a good way to demonstrate your skills as part of your project portfolio. Documenting the journey is another great way to showcase your experience online. Consider creating articles you can publish on platforms such as LinkedIn and Medium.

## Prerequisite and Setup

Before you begin, ensure you have the following:

- This guide assumes that you are using the AWS Cloud9 IDE. You are not obligated to use AWS Cloud9; however, if you choose to use a different IDE, you will be responsible for resolving any environment-specific issues that may arise.
- **AWS CLI** installed and configured with your AWS account.

---

---

---

## Step-by-step setup

These instructions will walk you through configuring your CDK App and Lambda code necessary for this capstone project. Please follow each step carefully to ensure your environment is correctly prepared.

#### Step 1 - CDK Configuration

Prepare your project environment and initialize a CDK application by executing the following commands in your AWS Cloud9 terminal:

a. Create a new directory for your project:
   ```bash
   mkdir properties_app

b. Navigate into your project directory:
   ```bash
   cd properties_app

c. Initialize a new CDK project with Python as the programming language:
   ```bash
   cdk init app --language python

d. Activate the Python virtual environment created by CDK:
   ```bash
   source .venv/bin/activate

e. Once the virtualenv is activated, you can install the required dependencies:
   ```bash
   pip install -r requirements.txt

f. Prepare your environment to deploy AWS resources with CDK:
   ```bash
   cdk bootstrap

g. Replace the existing content of 'properties_app/properties_app/properties_app_stack.py' with the following code to define your infrastructure:
```python
from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_notifications as s3_notif,
    RemovalPolicy,
    aws_lambda,
    aws_dynamodb as dynamodb
)

from constructs import Construct

class PropertiesAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3
        buckets = {'raw_properties': None, 'processed_properties': None}
        for id in buckets:
            buckets[id] = self.create_bucket(id)
        
        
        # DYNAMODB
        table = dynamodb.Table(self, 'PropertiesTable',
            partition_key=dynamodb.Attribute(
                name='zpid',
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
        
        
        # LAMBDA   
        lambda_cn = aws_lambda.Function(self, 'CurrencyStandardizer',
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.seconds(10),
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset("src/CurrencyStandardizer/")
        )
        
        
        # PERMISSIONS & EVENTS        
        buckets['raw_properties'].add_event_notification(s3.EventType.OBJECT_CREATED, s3_notif.LambdaDestination(lambda_cn))        
        buckets['raw_properties'].grant_read_write(lambda_cn)
        buckets['processed_properties'].grant_read_write(lambda_cn)
        
        table.grant_write_data(lambda_cn)
        
        
        # ENVIRONMENTAL VARS
        lambda_cn.add_environment('RAW_PROPERTIES_BUCKET', buckets['raw_properties'].bucket_name)
        lambda_cn.add_environment('PROCESSED_PROPERTIES_BUCKET', buckets['processed_properties'].bucket_name)
        lambda_cn.add_environment('PROPERTIES_TABLE_NAME', table.table_name)
            
    def create_bucket(self, id):
        bucket = s3.Bucket(self, id,
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True
        )
        
        return bucket
```
This script sets up your AWS cloud infrastructure, including two S3 buckets for handling raw and processed data, a DynamoDB table for data storage, and a Lambda function to process data. 
Each resource is configured with necessary permissions and environment variables to ensure smooth operation of your application.

h. Create the necessary directories and files for your Lambda function:
   ```bash
   mkdir -p src/CurrencyStandardizer && touch src/CurrencyStandardizer/event.json src/CurrencyStandardizer/template.yaml src/CurrencyStandardizer/lambda_function.py

i. Implement the logic for the Lambda function. Open 'properties_app/src/CurrencyStandardizer/lambda_function.py' and insert the following Python code:
```python
import json
import boto3
import csv
import io
import os
from decimal import Decimal

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # TODO: Replace placeholders with actual S3 bucket and DynamoDB table names
    processed_bucket = 'YOUR-PROCESSED-PROPERTIES-S3-BUCKET-NAME'
    table_name = 'YOUR-DYNAMODB-TABLE-NAME'

    # Retrieving the S3 object based on event triggers
    raw_bucket = event['Records'][0]['s3']['bucket']['name']
    csv_filename = event['Records'][0]['s3']['object']['key']
    obj = s3.get_object(Bucket=raw_bucket, Key=csv_filename)
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

        # TODO: Implement the currency conversion logic here
        
        processed_rows.append(filtered_row)
    
    # TODO: Implement logic to upload processed data to DynamoDB
    # TODO: Implement logic to move processed files to the processed bucket
    if processed_rows:
        upload_to_dynamodb(table_name, processed_rows)
        move_file_to_processed_bucket(raw_bucket, processed_bucket, csv_filename)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Currency Standardization complete!')
    }
    
# TODO: Complete the currency conversion function
def convert_currency(price, currency):
    # Example: return price * 0.75 if currency == 'CAD' else price
    pass  # Remove 'pass' and replace with your implementation of conversion based on currency type

# TODO: Complete the function to upload data to DynamoDB
# Check the AWS Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/index.html
def upload_to_dynamodb(table_name, items):
    pass  # Remove 'pass' and replace with your implementation of the DynamoDB batch writer to upload items

# TODO: Complete the function to move files within S3
# Check the AWS Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
def move_file_to_processed_bucket(raw_bucket_name, processed_bucket_name, file_key):
    pass  # Remove 'pass' and replace with your implementation of an S3 resource to copy and delete the original file
```
This setup ensures that the Lambda function is properly scripted to handle events triggered by new files in the S3 bucket, process those files according to your business logic, and interact correctly with other AWS services like DynamoDB and S3.


#### Step 2 - Deploy CDK App

After setting up the CDK stack, proceed to synthesize and deploy your application to ensure all resources are properly configured and created in AWS.

a. ```bash
   cdk synth # Generates the CloudFormation template for your app
b. ```bash
   cdk deploy # Deploys the CDK app to your AWS account

#### Step 3 - Configure the CurrencyStandardizer Lambda Function

a. Set up a test event for your Lambda function. Open 'properties_app/src/CurrencyStandardizer/event.json' and replace its contents with the following JSON. This event simulates an S3 trigger:
```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "YOUR-RAW-PROPERTIES-S3-BUCKET-NAME"
        },
        "object": {
          "key": "2024_apr_n9b.csv"
        }
      }
    }
  ]
}
```

b. Replace "YOUR-RAW-PROPERTIES-S3-BUCKET-NAME" above with the actual name of your raw properties S3 bucket created by CDK. This information can be found in the AWS S3 console or from the output of cdk deploy.

c. Find the the existing 'properties_app/src/CurrencyStandardizer/template.yaml' file in your file tree and replaces its contents with the code below. Remember to save your changes.
```yaml
Resources:
  CurrencyStandardizer:
    Type: AWS::Serverless::Function
    Properties:
      Handler: lambda_function.lambda_handler
      Runtime: python3.10
      CodeUri: .
```

d. Prepare and Upload the Data File. Create a CSV file that will be processed by your Lambda function. This file will contain mock data representing property listings with prices in both CAD and USD, 
among other details. Copy the provided CSV data below into your local text editor and save the file with the name `properties_data.csv`.

```csv
index_id,result_from,livingArea,state,open_house_info,lotAreaValue,shouldHighlight,daysOnZillow,priceForHDP,homeStatusForHDP,unit,streetAddress,bedrooms,city,zpid,listing_sub_type,isUnmappable,openHouse,zipcode,homeStatus,longitude,bathrooms,isPremierBuilder,isPreforeclosureAuction,isZillowOwned,latitude,isShowcaseListing,lotAreaUnit,homeType,price,isNonOwnerOccupied,isFeatured,country,currency
1,listing_url,,ON,,,false,-1,499900,FOR_SALE,,445 Bridge Ave,7,Windsor,347741185,[object Object],false,,N9B2M3,FOR_SALE,-83.05935,2,false,false,false,42.30826,false,,SINGLE_FAMILY,499900,true,false,CAN,CAD
2,listing_url,,ON,,,false,-1,299900,FOR_SALE,,194 Bridge Ave,5,Windsor,2064302558,[object Object],false,,N9B2M2,FOR_SALE,-83.06152,2,false,false,false,42.3127,false,,SINGLE_FAMILY,299900,true,false,CAN,CAD
3,listing_url,,ON,[object Object],,false,-1,349900,FOR_SALE,,1119 Josephine Ave,4,Windsor,347563003,[object Object],false,Sun. 2-4pm,N9B2L6,FOR_SALE,-83.05237,2,false,false,false,42.299076,false,,SINGLE_FAMILY,349900,true,false,CAN,CAD
4,listing_url,,ON,,,false,-1,569000,FOR_SALE,,215 Curry Ave,4,Windsor,2056507110,[object Object],false,,N9B2B4,FOR_SALE,-83.05766,3,false,false,false,42.313683,false,,SINGLE_FAMILY,569000,true,false,CAN,CAD
5,listing_url,,ON,,,false,-1,479888,FOR_SALE,,1930 Dominion Blvd,4,Windsor,347521193,[object Object],false,,N9B3H9,FOR_SALE,-83.03713,2,false,false,false,42.286583,false,,SINGLE_FAMILY,479888,true,false,CAN,CAD
6,listing_url,,ON,,4878.72,false,-1,999900,FOR_SALE,,528 California Ave,9,Windsor,347636995,[object Object],false,,N9B2Y9,FOR_SALE,-83.06371,3,false,false,false,42.305744,false,sqft,SINGLE_FAMILY,999900,true,false,CAN,CAD
7,listing_url,,ON,[object Object],,false,-1,299900,FOR_SALE,,915 Randolph Ave,4,Windsor,347399356,[object Object],false,Sat. 2-4pm,N9B2V1,FOR_SALE,-83.05876,2,false,false,false,42.30102,false,,SINGLE_FAMILY,299900,true,false,CAN,CAD
8,listing_url,,ON,,0,false,-1,549000,FOR_SALE,,1251 McKay Ave,6,Windsor,2064329093,[object Object],false,,N9B2A8,FOR_SALE,-83.046936,3,false,false,false,42.298733,false,sqft,SINGLE_FAMILY,549000,true,false,CAN,CAD
9,listing_url,,ON,,,false,-1,299888,FOR_SALE,,449 Curry Ave,4,Windsor,347327647,[object Object],false,,N9B2B8,FOR_SALE,-83.05505,2,false,false,false,42.30963,false,,SINGLE_FAMILY,299888,true,false,CAN,CAD
10,listing_url,,ON,[object Object],6054.84,false,-1,739999,FOR_SALE,,1731 California Ave,4,Windsor,347636176,[object Object],false,Sat. 2-4pm,N9B3T5,FOR_SALE,-83.05192,4,false,false,false,42.28652,false,sqft,SINGLE_FAMILY,739999,true,false,CAN,CAD
11,listing_url,,ON,,,false,-1,399000,FOR_SALE,,223 Campbell Ave,6,Windsor,347517993,[object Object],false,,N9B2H1,FOR_SALE,-83.06002,2,false,false,false,42.312798,false,,SINGLE_FAMILY,399000,true,false,CAN,CAD
12,listing_url,,ON,,,false,-1,699900,FOR_SALE,,2211 California Ave,5,Windsor,345458368,[object Object],false,,N9B3V5,FOR_SALE,-83.046135,2,false,false,false,42.2775,false,,SINGLE_FAMILY,699900,true,false,CAN,CAD
13,listing_url,,ON,,,false,-1,299000,FOR_SALE,,933 Bridge Ave,4,Windsor,2076522945,[object Object],false,,N9B2M9,FOR_SALE,-83.0553,2,false,false,false,42.301968,false,,SINGLE_FAMILY,299000,true,false,CAN,CAD
14,listing_url,,ON,[object Object],,false,-1,599900,FOR_SALE,# 909,915 Randolph Ave #909,10,Windsor,347526113,[object Object],false,Sat. 2-4pm,N9B2V1,FOR_SALE,-83.05876,4,false,false,false,42.30102,false,,SINGLE_FAMILY,599900,true,false,CAN,CAD
15,listing_url,783,ON,,,false,-1,199900,FOR_SALE,,1223 California Ave,2,Windsor,347329973,[object Object],false,,N9B2Z8,FOR_SALE,-83.057495,1,false,false,false,42.2952,false,,SINGLE_FAMILY,199900,true,false,CAN,CAD
16,listing_url,,ON,,,false,-1,299999,FOR_SALE,,371 Josephine Ave,4,Windsor,347239573,[object Object],false,,N9B2K9,FOR_SALE,-83.05927,1,false,false,false,42.30971,false,,SINGLE_FAMILY,299999,true,false,CAN,CAD
17,listing_url,,ON,,,false,-1,509000,FOR_SALE,,1206 McKay Ave,4,Windsor,2067882602,[object Object],false,,N9B2A9,FOR_SALE,-83.04679,2,false,false,false,42.299644,false,,SINGLE_FAMILY,509000,true,false,CAN,CAD
18,listing_url,,ON,[object Object],,false,-1,799900,FOR_SALE,,1550 Saint Clair Ave,6,Windsor,2061965423,[object Object],false,Sat. 1-4pm,N9B3K7,FOR_SALE,-83.0559,3,false,false,false,42.29084,false,,SINGLE_FAMILY,799900,true,false,CAN,CAD
19,listing_url,,ON,,,false,-1,379000,FOR_SALE,,962 Merritt Dr,3,Windsor,347048689,[object Object],false,,N9B3C5,FOR_SALE,-83.05726,2,false,false,false,42.29989,false,,SINGLE_FAMILY,379000,true,false,CAN,CAD
20,listing_url,,ON,,,false,-1,399000,FOR_SALE,,649 Bridge Ave,4,Windsor,343557375,[object Object],false,,N9B2M5,FOR_SALE,-83.05782,1,false,false,false,42.30588,false,,SINGLE_FAMILY,399000,true,false,CAN,CAD
```

Find the raw properties S3 bucket, which was created during the CDK deployment and then upload the `properties_data.csv`.

---

---

---

## Implementation Steps

Develop the Lambda function in 'properties_app/src/CurrencyStandardizer/lambda_function.py' to read CSV files from the S3 bucket, convert currency values, and write the processed data to DynamoDB.
- The function should trigger on new files uploaded to the raw data bucket.
- Use Python libraries such as boto3 and csv for AWS interactions and data manipulation.



#### Step 1 - Lambda Function Code Updates

Follow the `TODO` comments in the `lambda_function.py` file to implement the necessary functionality:

- Implement currency conversion in the `convert_currency` function.
- Implement data uploading in the `upload_to_dynamodb` function.
- Implement file movement logic in the `move_file_to_processed_bucket` function.

This structure encourages you to apply the concepts learned during the course and use AWS documentation where necessary.


#### Step 2 - Lambda Function Testing

Test the functionality of your Lambda function locally using SAM Local. To test, navigate to the properties_app/src/CurrencyStandardizer/ and execute the SAM command:

a. ```bash
    cd src/CurrencyStandardizer/
b. ```bash
    sam local invoke -e event.json

#### Step 3 - CDK: Deploy CDK App

Once you have fully tested the 'CurrencyStandardizer' lambda function and validated full functionality navigate to the 'properties_app' directory and deploy the CDK App.

a. ```bash
   cd ../../
b. ```bash
    cdk synth
c. ```bash
    cdk deploy 

#### Step 4 - End-to-End Testing with New Data

After deploying your application it's essential to verify that the system works with new data under real conditions. 
This step will help ensure that your application can handle new uploads and process them correctly.

a. Create a second CSV file with mock data. Copy the provided CSV data below into your local text editor and save the file with the name `properties_data2.csv`.

```csv
index_id,result_from,datePriceChanged,livingArea,state,open_house_info,lotAreaValue,shouldHighlight,daysOnZillow,priceForHDP,taxAssessedValue,providerListingID,homeStatusForHDP,unit,streetAddress,bedrooms,priceSuffix,rentZestimate,newConstructionType,city,zpid,listing_sub_type,isUnmappable,openHouse,zipcode,homeStatus,longitude,bathrooms,isPremierBuilder,isPreforeclosureAuction,group_type,isZillowOwned,latitude,zestimate,isShowcaseListing,lotAreaUnit,homeType,price,priceReduction,isNonOwnerOccupied,priceChange,isFeatured,country,timeOnZillow,currency
21,listing_url,1710918000000,1331,MI,,,false,35,359590,,29552886,FOR_SALE,# Q443JG,"Aspen at Avery Place Plan, Avery Place",2,+,2075,BUILDER_PLAN,Detroit,2053935271,[object Object],false,,48208,FOR_SALE,-83.08248,2,true,false,BUILDER_COMMUNITY,false,42.353264,345900,false,,TOWNHOUSE,359590,,true,15500,false,USA,3099533000,USD
22,listing_url,,1200,MI,[object Object],,false,53,409900,1400,,FOR_SALE,# 2,4130 Trumbull St #2,2,,2868,NEW_CONSTRUCTION_TYPE_OTHER,Detroit,331229732,[object Object],false,Sun. 1:30-3:30pm,48208,FOR_SALE,-83.0749,2,false,false,,false,42.346146,404300,false,,CONDO,409900,,true,,false,USA,4645515000,USD
23,listing_url,,0,MI,,0,false,38,0,,29619734,FOR_SALE,# SPJAK1,"Homes Available Soon, Scripps District",,+,2546,BUILDER_PLAN,Detroit,345613665,[object Object],false,,48208,FOR_SALE,-83.07364,,true,false,BUILDER_COMMUNITY,false,42.344063,,false,sqft,MULTI_FAMILY,0,,true,,false,USA,3313944000,USD
24,listing_url,,1150,MI,,4356,false,35,150000,42100,,FOR_SALE,,3722 Tillman St,4,,1385,,Detroit,88536279,[object Object],false,,48208,FOR_SALE,-83.09288,1,false,false,,false,42.33759,145300,false,sqft,SINGLE_FAMILY,150000,,true,,false,USA,3106215000,USD
25,listing_url,1698994800000,1331,MI,[object Object],,false,170,344090,,29552886,FOR_SALE,,1809 Merrick 5 St,2,,2348,BUILDER_SPEC,Detroit,2053935270,[object Object],false,Sat. 2:30-4pm,48208,FOR_SALE,-83.08248,3,true,false,,false,42.353264,333700,false,,TOWNHOUSE,344090,,true,-5000,false,USA,14754315000,USD
26,listing_url,,1418,MI,[object Object],,false,46,429900,1400,,FOR_SALE,# 6,4130 Trumbull St #6,2,,2997,,Detroit,331229736,[object Object],false,Sun. 1:30-3:30pm,48208,FOR_SALE,-83.0749,2,false,false,,false,42.346146,424600,false,,CONDO,429900,,true,,false,USA,4040715000,USD
27,listing_url,1707897600000,1936,MI,[object Object],,false,192,675000,,28731866,FOR_SALE,,1361 W Canfield St,3,,4652,BUILDER_SPEC,Detroit,2064260820,[object Object],false,Sat. 12-4pm,48208,FOR_SALE,-83.07499,3,true,false,,false,42.34842,658200,false,,CONDO,675000,,true,5000,false,USA,16655115000,USD
28,listing_url,1708502400000,1250,MI,,,false,115,385750,,,FOR_SALE,# 9,3415 Cochrane St #9,2,,2628,NEW_CONSTRUCTION_TYPE_OTHER,Detroit,2053655118,[object Object],false,,48208,FOR_SALE,-83.07453,3,false,false,,false,42.340443,373300,false,,TOWNHOUSE,385750,,true,3000,false,USA,10002315000,USD
29,listing_url,,1545,MI,,,false,668,99000,3500,,FOR_SALE,,4463 23rd St,4,,1700,,Detroit,88244778,[object Object],false,,48208,FOR_SALE,-83.09765,2,false,false,,false,42.341953,,false,,CONDO,99000,,true,,false,USA,57781515000,USD
30,listing_url,1711954800000,,MI,,0.37,false,103,900000,,,FOR_SALE,,5045 Trumbull St,,,1514,,Detroit,2056052463,[object Object],false,,48208,FOR_SALE,-83.07947,0,false,false,,false,42.352657,,false,acres,MULTI_FAMILY,900000,"$195,000 (Apr 1)",true,-195000,false,USA,8910662000,USD
31,listing_url,,1248,MI,,3920.4,false,74,20000,5600,,FOR_SALE,,2661 Nebraska St,3,,1314,,Detroit,88560172,[object Object],false,,48208,FOR_SALE,-83.09931,1,false,false,,false,42.357983,,false,sqft,SINGLE_FAMILY,20000,,true,,false,USA,6459915000,USD
32,listing_url,,1215,MI,,,false,72,398500,,,FOR_SALE,# 9,5216 Avery St #9,2,,2802,,Detroit,2052986954,[object Object],false,,48208,FOR_SALE,-83.08205,2,false,false,,false,42.353645,394900,false,,TOWNHOUSE,398500,,true,,false,USA,6287115000,USD
33,listing_url,,1350,MI,[object Object],,false,52,419900,1400,,FOR_SALE,# 4,4130 Trumbull St #4,2,,2936,,Detroit,331229734,[object Object],false,Sun. 1:30-3:30pm,48208,FOR_SALE,-83.0749,2,false,false,,false,42.346146,413900,false,,CONDO,419900,,true,,false,USA,4559115000,USD
34,listing_url,1709020800000,1916,MI,[object Object],,false,72,670000,,28731866,FOR_SALE,,4322 Lincoln St,3,,4588,BUILDER_SPEC,Detroit,2058139627,[object Object],false,Sat. 12-4pm,48208,FOR_SALE,-83.07486,3,true,false,,false,42.348,657100,false,,CONDO,670000,,true,5000,false,USA,6287115000,USD
35,listing_url,,2300,MI,,3920.4,false,71,250000,49600,,FOR_SALE,,3582 Tillman St,4,,1429,,Detroit,88546691,[object Object],false,,48208,FOR_SALE,-83.09247,1,false,false,,false,42.336884,240900,false,sqft,SINGLE_FAMILY,250000,,true,,false,USA,6178014000,USD
36,listing_url,,2326,MI,,3484.8,false,101,99900,18800,,FOR_SALE,,6073 15th St,,,1064,,Detroit,88304460,[object Object],false,,48208,FOR_SALE,-83.093796,2,false,false,,false,42.358505,99200,false,sqft,MULTI_FAMILY,99900,,true,,false,USA,8792715000,USD
37,listing_url,1711436400000,1545,MI,,,false,71,499999,,,FOR_SALE,,3305 Cochrane St,3,,3542,,Detroit,2068538379,[object Object],false,,48208,FOR_SALE,-83.074196,3,false,false,,false,42.339523,484800,false,,TOWNHOUSE,499999,"$10,000 (Mar 26)",true,-10000,false,USA,6200715000,USD
38,listing_url,1709193600000,1916,MI,[object Object],,false,44,675000,,28731866,FOR_SALE,,4321 Lincoln St,3,,4589,BUILDER_SPEC,Detroit,2054863225,[object Object],false,Sat. 12-4pm,48208,FOR_SALE,-83.07521,3,true,false,,false,42.34789,671700,false,,CONDO,675000,,true,9800,false,USA,3867915000,USD
39,listing_url,,1592,MI,,,false,295,556500,,,FOR_SALE,Unit 7,5220 Avery St UNIT 7,3,,3837,,Detroit,2056977261,[object Object],false,,48208,FOR_SALE,-83.08195,3,false,false,,false,42.35401,540100,false,,TOWNHOUSE,556500,,true,,false,USA,25554315000,USD
40,listing_url,,1278,MI,,,false,295,408500,,,FOR_SALE,Unit 2,5220 Avery St UNIT 2,2,,2817,,Detroit,2056978188,[object Object],false,,48208,FOR_SALE,-83.08195,3,false,false,,false,42.35401,397300,false,,TOWNHOUSE,408500,,true,,false,USA,25554315000,USD
41,listing_url,,946,MI,,6534,false,165,500000,17400,,FOR_SALE,,1748 Ferry Park St,1,,1034,,Detroit,88405087,[object Object],false,,48208,FOR_SALE,-83.0888,1,false,false,,false,42.363125,,false,sqft,SINGLE_FAMILY,500000,,true,,false,USA,14322315000,USD
```

b. Find the raw properties S3 bucket, which was created during the CDK deployment and then upload the `properties_data2.csv`.

c. **Monitor the Lambda Function**: After uploading the file, the Lambda function should automatically trigger. Go to the AWS Lambda service in the AWS Console. Open your CurrencyStandardizer function.
Check the monitoring tab and view logs in CloudWatch to verify that the function executed as expected.

d.  **Verify Data in DynamoDB**: Navigate to the DynamoDB service in the AWS Console. Open the table used by your Lambda function (e.g., PropertiesTable). 
Browse the items in the table to ensure that the new entries from properties_data2.csv are correctly processed and stored.

####  Step 5 - Cleanup Instructions

To remove the resources created by AWS CDK, follow these steps:

a. Navigate to the root directory of your CDK project

b. Run the following command to destroy the resources:
   ```bash
   cdk destroy

This command will remove all resources specified in your CDK application from your AWS account, ensuring that you are not charged for resources that are no longer in use.

---

---

---

## Troubleshooting & Getting Help

**Troubleshooting Tips**
- Lambda Function Errors: If the Lambda function fails, check the CloudWatch logs for error messages that can help you identify what went wrong.
- Data Issues: Ensure that the data format in your CSV matches the expected format in your Lambda function.
- Permissions Issues: Verify that your Lambda function has the necessary permissions to read from the S3 bucket and write to the DynamoDB table.

**You can always find assistance available for your cohort in the Slack channels.**


## Additional Challenge

Expand your application’s functionality by integrating real-time currency conversion rates instead of using hardcoded values. 
This will make your application more robust and adaptable to real-world conditions.