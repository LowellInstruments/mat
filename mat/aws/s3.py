import os
import boto3
from botocore.config import Config


def get_aws_s3_client():
    _k = os.getenv('DDH_AWS_KEY_ID')
    _s = os.getenv('DDH_AWS_SECRET')
    _cnf = Config(connect_timeout=5, retries={'max_attempts': 0})
    return boto3.client('s3',
                        aws_access_key_id=_k,
                        aws_secret_access_key=_s,
                        region_name='us-east-1',
                        config=_cnf)
