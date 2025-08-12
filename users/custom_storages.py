from storages.backends.s3boto3 import S3Boto3Storage

class NoHeadObjectS3Boto3Storage(S3Boto3Storage):
    def exists(self, name):
        return False