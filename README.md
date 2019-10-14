# Image-to-Textract-Response
Analyse an image in a source S3 bucket with AWS Textract, and store the JSON response to a destination S3 bucket.

Please double check you are in the AWS region you intend; this needs to be the **same region** as the bucket which will contain the images you wish to analyse.

## S3 Trigger
This function can respond to S3 ObjectCreated events. 

To configure the trigger, on the Lambda function, in "Designer > Add triggers", click "S3". The "Configure triggers" dialog appears.
Select a bucket (any time a pdf is added to this bucket, the function will run).

Verify that "all object create events" is selected (or choose PUT POST or COPY).

Click "Add" (bottom right), then "Save" (top right).

## Environment Variables

On the same screen in the Lambda Management Console for this function, scroll down to "Environment Variables":

The SAM deployment automatically creates an S3 Destination bucket in which JSON Textract responses are stored. This is the default value for the DESTINATION_TEXTRACTRESPONSE_BUCKET environment variable.
You can change the DESTINATION_TEXTRACTRESPONSE_BUCKET environment variable to point to any existing S3 bucket, as long as the associated IAM permissions allow PutObject permissions on that bucket.

### Required:

**DESTINATION_BUCKET**: the name of the S3 bucket to which the PDF will be saved (if blank, it should write to the input event bucket)

## Execution Role

Ensure that your execution role has both "s3:GetObject" and "s3:PutObject" permissions the source and destination buckets, respectively.

The easiest is to open the Lambda Function settings, scroll down to the **Execution Role** section, and click "View the
 *** role" on the IAM console.  Confirm that the role's policies includes S3 permissions, e.g.:

 ```
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::*"
        }
```

Without GetObject permission on the triggering bucket and PutObject permission on the output bucket, you'll get Access Denied errors.

## Confirm successful installation
### S3 Trigger
If you configured the S3 trigger, you can try it, by dropping an image into the S3 bucket you have set the trigger on.

To verify it works, look for a JSON response in the output bucket, or check the logs in CloudWatch (under the Lambda monitoring tab).

### Sizing Notes
If you observe "Process exited before completing request" errors, it might point to your Lambda function not having sufficient access to sufficient resources, or having insufficient time-out period.
##### Memory
Experience suggests assigning *500MB*.  
This can be set under the "Memory (MB)" header in the "Basic settings" section of the Lambda function configuration tab.

##### Timeout
The time taken for the Lambda to run, will depend on the size of the PDF document being processed.  For maximum flexibility, allow a 30 second timeout, although experience suggests that the function should hardly ever take longer than a few seconds to run. 

This can be set under the "Timeout" header in the "Basic settings" section of the Lambda function configuration tab.
