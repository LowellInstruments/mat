from mat.aws.s3 import get_aws_s3_client


class TestAwsS3:
    def test_aws_s3_get_client(self):
        assert get_aws_s3_client()
