import json

#!pip3 import sagemaker
#!pip3 import boto3

import sagemaker
import boto3
from sagemaker.huggingface import HuggingFaceModel
import csv
import os

#Copy the following in the doc : ~/.aws/credentials
#[default]
#region = 
#aws_access_key_id =
#aws_secret_access_key = 

# aws_role = sagemaker.get_execution_role()
aws_role = 'arn:aws:iam::284762642143:role/service-role/AmazonSageMaker-ExecutionRole-20240111T142380'


sess = sagemaker.Session(boto3.session.Session())

    # # Hugging Face Model configuration. https://huggingface.co/models
    # hub = {
    #     'HF_MODEL_ID': 'mdarhri00/named-entity-recognition',
    #     'HF_TASK': 'token-classification'
    # }

    # # Create Hugging Face Model Class
    # huggingface_model = HuggingFaceModel(
    #     transformers_version='4.26.0',
    #     pytorch_version='1.13.1',
    #     py_version='py39',
    #     env=hub,
    #     role=aws_role,
    # )
    #
    # # Deploy model to SageMaker Inference.
    # predictor = huggingface_model.deploy(
    #     initial_instance_count=1,  # Number of instances
    #     instance_type='ml.m5.xlarge'  # EC2 instance type
    # )
    # endpoint_name = predictor.endpoint_name

endpoint_name='huggingface-pytorch-inference-2024-01-18-19-45-30-010'

predictor = sagemaker.predictor.Predictor(
    endpoint_name=endpoint_name,
    serializer=sagemaker.base_serializers.JSONSerializer(),
)

#Make a prediction using the deployed model
#Just an example line to demo model
# result = predictor.predict({
#     "inputs": "My name is Sarah Jessica Parker but you can call me Jessica and I live in College Park",
# })

# result_json = json.loads(result)

# for entry in result_json:
#   print(entry)

#NOTE for error regarding (ResourceLimitExceeded) you have to go to SageMaker and search "increase quota" then search "ml.m5.xlarge" and request more quotas each time. Then re-run the code.


def process_files_from_s3(bucket, prefix, output_csv_file, threshold=0.8):
    """
    Processes files from an S3 bucket and writes the prediction results to a CSV file.

    :param bucket: S3 bucket name
    :param prefix: S3 prefix to filter the objects to be processed
    :param output_csv_file: Path to the output CSV file
    :param threshold: Confidence threshold for filtering predictions
    """
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    data_to_write = []

    for obj in response.get('Contents', []):
        file_key = obj['Key']

        # Read the content directly from S3
        s3_object = s3_client.get_object(Bucket=bucket, Key=file_key)
        content = s3_object['Body'].read().decode('utf-8')

        # Make a prediction using the deployed model
        result = predictor.predict({"inputs": content})
        result_json = json.loads(result)

        # Process and append results to data_to_write
        for entry in result_json:
            if entry['score'] >= threshold:  # Filter based on confidence threshold
                data_to_write.append([file_key, entry['text'], entry['type'], entry['score']])

    # Write the data to a CSV file
    with open(output_csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['File Name', 'Extracted Text', 'Entity Type', 'Confidence Score'])
        writer.writerows(data_to_write)

# Example usage of the function
    process_files_from_s3(
        bucket='sagemaker-studio-284762642143-l7zk0dm3e7k',
        prefix='testrun1',
        output_csv_file='output_predictions.csv')
    

print("hello world")