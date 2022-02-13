from aws_cdk import (
    core as cdk,
    aws_s3 as s3,
    aws_s3_deployment as deployment
)
from constructs import Construct
import _constants as constants


class SPAStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.create_bucket()
        self.deploy_template()

    def create_bucket(self):
        print("Creating S3 bucket with prefix: ", constants.s3WebsiteBucketId)
        cors_rule = s3.CorsRule(
            allowed_headers=["*"],
            allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD],
            allowed_origins=["*"]
        )

        self._host_bucket = s3.Bucket(
            self, constants.s3WebsiteBucketId,
            versioned=True,
            cors=[cors_rule],
            object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
            website_index_document=constants.indexDocument,
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        self._host_bucket.grant_public_access()

    def deploy_template(self):
        deployment.BucketDeployment(
            self, "InitialContent",
            sources=[deployment.Source.asset(constants.s3DeploymentFolder)],
            destination_bucket=self._host_bucket)
