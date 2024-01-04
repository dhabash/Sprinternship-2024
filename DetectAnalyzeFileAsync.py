from detectFileAsync import DocumentProcessor
import boto3
import pandas as pd

    # Detect sentiment
def sentiment_analysis(detected_text, lang):

        comprehend = boto3.client("comprehend")

        detect_sent_response = comprehend.batch_detect_sentiment(
                TextList=detected_text, LanguageCode=lang)

        # Lists to hold sentiment labels and sentiment scores
        sentiments = []
        pos_score = []
        neg_score = []
        neutral_score = []
        mixed_score = []

        # for all results add the Sentiment label and sentiment scores to lists
        for res in detect_sent_response['ResultList']:
            sentiments.append(res['Sentiment'])
            print(res['SentimentScore'])
            print(type(res['SentimentScore']))
            for key, val in res['SentimentScore'].items():
                if key == "Positive":
                    pos_score.append(val)
                if key == "Negative":
                    neg_score.append(val)
                if key == "Neutral":
                    neutral_score.append(val)
                if key == "Mixed":
                    mixed_score.append(val)

        return sentiments, pos_score, neg_score, neutral_score, mixed_score
        
    # detect entities
def entity_detection(detected_text, lang):

        comprehend = boto3.client("comprehend")

        # convert and handle string here
        # do string handling
        detect_ent_response = comprehend.batch_detect_entities(
            TextList=detected_text, LanguageCode=lang)

        # To fold detected entities and entity types
        ents = []
        types = []

        # Get detected entities and types from the response returned by Comprehend
        for i in detect_ent_response['ResultList']:
            if len(i['Entities']) == 0:
                ents.append("N/A")
                types.append("N/A")
            else:
                sentence_ents = []
                sentence_types = []
                for entities in i['Entities']:
                    sentence_ents.append(entities['Text'])
                    sentence_types.append(entities['Type'])
                ents.append(sentence_ents)
                types.append(sentence_types)

        return ents, types

    # Detect key phrases
def key_phrases_detection(detected_text, lang):

        comprehend = boto3.client("comprehend")

        key_phrases = []
        detect_phrases_response = comprehend.batch_detect_key_phrases(
            TextList=detected_text, LanguageCode=lang)
        for i in detect_phrases_response['ResultList']:
            if len(i['KeyPhrases']) == 0:
                key_phrases.append("N/A")
            else:
                phrases = []
                for phrase in i['KeyPhrases']:
                    phrases.append(phrase['Text'])
                key_phrases.append(phrases)

        return key_phrases     
        
def process_document(roleArn, bucket, document, region_name):

        # Create analyzer class from DocumentProcessor, create a topic and queue, use Textract to get text,
        # then delete topica and queue
        analyzer = DocumentProcessor(roleArn, bucket, document, region_name)
        analyzer.CreateTopicandQueue()
        extracted_text = analyzer.ProcessDocument()
        analyzer.DeleteTopicandQueue()

        # detect dominant language
        comprehend = boto3.client("comprehend")
        response = comprehend.detect_dominant_language(Text=str(extracted_text[:10]))
        print(response)
        print(type(response))
        lang = ""
        for i in response['Languages']:
            lang = i['LanguageCode']
        print(lang)

        # or you can enter language code below
        # lang = "en"

        print("Lines in detected text:" + str(len(extracted_text)))
        sliced_list = []
        start = 0
        end = 24
        while end < len(extracted_text):
            sliced_list.append(extracted_text[start:end])
            start += 25
            end += 25
        print(sliced_list)

        # Create lists to hold analytics data, these will be turned into columns
        all_sents = []
        all_scores = []
        all_ents = []
        all_types = []
        all_key_phrases = []
        all_pos_ratings = []
        all_neg_ratings = []
        all_neutral_ratings = []
        all_mixed_ratings = []

        # For every slice, get sentiment analysis, entity detection and key phrases, append results to lists
        for slice in sliced_list:
            slice_labels, pos_ratings, neg_ratings, neutral_ratings, mixed_ratings = sentiment_analysis(slice, lang)
            all_sents.append(slice_labels)
            all_pos_ratings.append(pos_ratings)
            all_neg_ratings.append(neg_ratings)
            all_neutral_ratings.append(neutral_ratings)
            all_mixed_ratings.append(mixed_ratings)
            slice_ents, slice_types = entity_detection(slice, lang)
            all_ents.append(slice_ents)
            all_types.append(slice_types)
            key_phrases = key_phrases_detection(slice, lang)
            all_key_phrases.append(key_phrases)

        # List comprehension to flatten multiple lists into a single list
        extracted_text = [line for sublist in sliced_list for line in sublist]
        all_sents = [sent for sublist in all_sents for sent in sublist]
        all_scores = [score for sublist in all_scores for score in sublist]
        all_ents = [ents for sublist in all_ents for ents in sublist]
        all_types = [types for sublist in all_types for types in sublist]
        all_key_phrases = [kp for sublist in all_key_phrases for kp in sublist]
        all_mixed_ratings = [kp for sublist in all_mixed_ratings for kp in sublist]
        all_pos_ratings = [kp for sublist in all_pos_ratings for kp in sublist]
        all_neg_ratings = [kp for sublist in all_neg_ratings for kp in sublist]
        all_neutral_ratings = [kp for sublist in all_neutral_ratings for kp in sublist]

        print(len(extracted_text))
        print(len(all_sents))
        print(len(all_ents))
        print(len(all_types))
        print(len(all_key_phrases))

        print("List of Recognized Entities:")

        # Create dataframe and save as CSV
        df = pd.DataFrame({'Sentences':extracted_text, 'Sentiment':all_sents, 'SentPosScore':all_pos_ratings,
                        'SentNegScore':all_neg_ratings, 'SentNeutralScore':all_neutral_ratings, 'SentMixedRatings':all_mixed_ratings,
                        'Entities':all_ents, 'EntityTypes':all_types,'KeyPhrases:':all_key_phrases})
        analysis_results = str(document.replace(".","_") + "_" + "analysis" + ".csv")
        df.to_csv(analysis_results, index=False)

        print(df)
        print("Data written to file!")

        return extracted_text, analysis_results     
        
def main():

        # Initialize S3 client and set RoleArn, region name, and bucket name
        s3 = boto3.client("s3")
        roleArn = 'arn:aws:s3:::textractsamplesprint2024/whpool_single_message_plain_text_example_1.pdf'
        region_name = 'us-east-2'
        bucket_name = 'textractsamplesprint2024'

        # initialize global corpus
        full_corpus = []

        # to hold all docs in bucket
        docs_list = []

        # loop through docs in bucket, get names of all docs
        s3_resource = boto3.resource("s3")
        bucket = s3_resource.Bucket(bucket_name)
        for bucket_object in bucket.objects.all():
            docs_list.append(bucket_object.key)
        print(docs_list)

        # For all the docs in the bucket, invoke document processing function,
        # add detected text to corpus of all text in batch docs,
        # and save CSV of comprehend analysis data and textract detected to S3
        for i in docs_list:
            detected_text, analysis_results = process_document(roleArn, bucket_name, i, region_name)
            full_corpus.append(detected_text)
            print("Uploading file: {}".format(str(analysis_results)))
            name_of_file = str(analysis_results)
            s3.upload_file(name_of_file, bucket_name, name_of_file)

        # print the global corpus
        print(full_corpus)

if __name__ == "__main__":
        main()     
        