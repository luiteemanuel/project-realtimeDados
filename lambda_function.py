import json
import boto3 
import os 
import requests 

TOMORROW_API_KEY = os.getenv('TOMORROW_API_KEY')
latitude = -15.31227249
longitude = -49.11664409

url = f'https://api.tomorrow.io/v4/weather/forecast?location={latitude},{longitude}&apikey={TOMORROW_API_KEY}'
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

STREAM_NAME = 'broker'
REGION_NAME = 'us-east-1'

kinesis_client = boto3.client('kinesis', region_name=REGION_NAME)

def lambda_handler(event, context):
    response = requests.get(url, headers=headers)
    weather_data = response.json()
    
    kinesis_client.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(weather_data),
        PartitionKey='partition_key'
    )


    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }