
import boto3
import json
import sys
import time

class DocumentProcessor:

    jobId = ''
    region_name = 'US East (Ohio) us-east-2'

    roleArn = 'arn:aws:s3:::textractsamplesprint2024/whpool_single_message_plain_text_example_1.pdf'
    bucket = 'textractsamplesprint2024'
    document = 'whpool_single_message_plain_text_example_1.pdf'

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, document, region):
        self.roleArn = role
        self.bucket = bucket
        self.document = document
        self.region_name = region

        # Instantiates necessary AWS clients
        session = boto3.Session(profile_name='profile-name',
        region_name='self.region_name')
        self.textract = session.client('textract', region_name=self.region_name)
        self.sqs = session.client('sqs', region_name=self.region_name)
        self.sns = session.client('sns', region_name=self.region_name)

    def CreateTopicandQueue(self):

        millis = str(int(round(time.time() * 1000)))

        # Create SNS topic
        snsTopicName = "AmazonTextractTopic" + millis

        topicResponse = self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        # create SQS queue
        sqsQueueName = "AmazonTextractQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                AttributeNames=['QueueArn'])['Attributes']

        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        # Authorize SNS to write SQS queue
        policy = """{{
  "Version":"2012-10-17",
  "Statement":[
    {{
      "Sid":"MyPolicy",
      "Effect":"Allow",
      "Principal" : {{"AWS" : "*"}},
      "Action":"SQS:SendMessage",
      "Resource": "{}",
      "Condition":{{
        "ArnEquals":{{
          "aws:SourceArn": "{}"
        }}
      }}
    }}
  ]
}}""".format(sqsQueueArn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl=self.sqsQueueUrl,
            Attributes={
                'Policy': policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)
    

#ABOVE IS PART 1

import boto3
import json
import sys
import time

def ProcessDocument(self):
    
            # Checks if job found
            jobFound = False
    
            # Starts the text detection operation on the documents in the provided bucket
            # Sends status to supplied SNS topic arn
            response = self.textract.start_document_text_detection(
                    DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                    NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
            print('Processing type: Detection')
    
            print('Start Job Id: ' + response['JobId'])
            dotLine = 0
            while jobFound == False:
                sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                                    MaxNumberOfMessages=10)
    
                # Waits until messages are found in the SQS queue
                if sqsResponse:
                    if 'Messages' not in sqsResponse:
                        if dotLine < 40:
                            print('.', end='')
                            dotLine = dotLine + 1
                        else:
                            print()
                            dotLine = 0
                        sys.stdout.flush()
                        time.sleep(5)
                        continue
    
                    # Checks for a completed job that matches the jobID in the response from
                    # StartDocumentTextDetection
                    for message in sqsResponse['Messages']:
                        notification = json.loads(message['Body'])
                        textMessage = json.loads(notification['Message'])
                        if str(textMessage['JobId']) == response['JobId']:
                            print('Matching Job Found:' + textMessage['JobId'])
                            jobFound = True
                            text_data = self.GetResults(textMessage['JobId'])
                            self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                                    ReceiptHandle=message['ReceiptHandle'])
                            return text_data
                        else:
                            print("Job didn't match:" +
                                str(textMessage['JobId']) + ' : ' + str(response['JobId']))
                        # Delete the unknown message. Consider sending to dead letter queue
                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                                ReceiptHandle=message['ReceiptHandle'])
    
            print('Done!')
        
    # gets the results of the completed text detection job
    # checks for pagination tokens to determine if there are multiple pages in the input doc
def GetResults(self, jobId):
        maxResults = 1000
        paginationToken = None
        finished = False

        while finished == False:
            response = None
            if paginationToken == None:
                response = self.textract.get_document_text_detection(JobId=jobId,
                                                                         MaxResults=maxResults)
            else:
                response = self.textract.get_document_text_detection(JobId=jobId,
                                                                         MaxResults=maxResults,
                                                                         NextToken=paginationToken)

            blocks = response['Blocks']

            # List to hold detected text
            detected_text = []

            # Display block information and add detected text to list
            for block in blocks:
                if 'Text' in block and block['BlockType'] == "LINE":
                    detected_text.append(block['Text'])

            # If response contains a next token, update pagination token
            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

            return detected_text
        