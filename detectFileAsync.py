import boto3
import json
import sys
import time

def ProcessDocument(self):
    
            #  Checks if job found
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
    #sdfgh