import boto3
import json
import urllib
import io
import os

from botocore.client import Config
from PIL import Image

config = Config(retries=dict(max_attempts=50))
textract_client = boto3.client(
    service_name='textract',
    region_name='us-east-1',
    endpoint_url='https://textract.us-east-1.amazonaws.com',
    config=config
)
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')


DESTINATION_BUCKET = None
if 'DESTINATION_TEXTRACTRESPONSE_BUCKET' in os.environ:
    DESTINATION_BUCKET = str(os.environ['DESTINATION_TEXTRACTRESPONSE_BUCKET'])
    print(f"Setting the destination bucket: {DESTINATION_BUCKET}. "
                 f"Be sure to set the S3 bucket trigger on the Lambda's configuration")
else:
    raise Exception(f"Couldn't process the DESTINATION_TEXTRACTRESPONSE_BUCKET environment variable. "
                    f"The DESTINATION_TEXTRACTRESPONSE_BUCKET needs to be set to a valid S3 bucket to which the user has full access.")


def get_image(bucket, key) -> (Image.Image, dict):
    """
    Download an image from the S3 bucket and key (directory + filename) provided.
    :param bucket:  The S3 Bucket in which to find the image.
    :param key:  The key of the image (last part of the key).
    :return:  A PIL Image downloaded from the bucket.
    """
    print(f"Fetching item (bucket: '{bucket}', key: '{key}') from S3.")

    bucket = s3_resource.Bucket(bucket)
    object = bucket.Object(key)
    response = object.get()
    file_stream = response['Body']
    metadata = response['Metadata']
    print("Successfully retrieved S3 object.")

    print("Converting to a PIL Image.")
    im = Image.open(file_stream)
    return im, metadata


def image_to_response(image: Image.Image) -> dict:
    """
    Call Textract using the passed image and return the response.
    :param image: The image (of class PIL Image) to send to Textract.
    :return: A dictionary containing the Textract response.
    """

    # Convert the Image into Bytes
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes = image_bytes.getvalue()

    print("Submitting document to Textract.")
    # Send the Image to Textract
    textract_response = textract_client.analyze_document(
        Document={'Bytes': image_bytes},
        FeatureTypes=['TABLES']
    )
    print("Textract analyzed document successfully")
    return textract_response


def save_response(textract_response: dict, bucket_name: str, key: str, metadata: dict) -> None:
    """
    Store the Textract responses received to an S3 bucket.

    :param textract_response: The textract response to be stored.
    :param bucket_name: The S3 bucket in which to store the response.
    :param file_name: The filename of the response to use when storing it.
    :return:
    """
    json_array = json.dumps(textract_response)

    print("Saving the Textract response to S3 with bucket: {bucket_name}, key: {location}.")
    s3_resource.Object(bucket_name, key).put(
        Body=json_array,
        Metadata=metadata
    )


# --------------- Main handler ------------------
def lambda_handler(event, context):
    '''
    Uses Rekognition APIs to detect text and labels for objects uploaded to S3
    and store the content in DynamoDB.
    '''
    # Log the the received event locally.
    # print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event.
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    image, metadata = get_image(bucket, key)

    metadata['SOURCE_IMAGE_KEY'] = key
    metadata['SOURCE_IMAGE_BUCKET'] = bucket

    response = image_to_response(image)

    destination_key = ''.join(key.split('.')[:-1]) + '.json'
    save_response(response, DESTINATION_BUCKET, destination_key, metadata)
