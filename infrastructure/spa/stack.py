from aws_cdk import (
    core as cdk,
    aws_s3 as s3,
    aws_s3_deployment as deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_wafv2 as waf
)
from constructs import Construct
import _constants as constants


class SPAStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.create_bucket()
        self.deploy_template()
        self.create_distribution()

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

    def create_distribution(self):
        # WAF custom rule
        custom_rule = waf.CfnWebACL.RuleProperty(
            name="DemoStaticWebsiteWebACL-AdminURI",
            priority=100,
            action=waf.CfnWebACL.RuleActionProperty(
                block=waf.CfnWebACL.BlockActionProperty(
                    custom_response=waf.CfnWebACL.CustomResponseProperty(
                        response_code=401
                    )
                )
            ),
            statement=waf.CfnWebACL.StatementProperty(
                byte_match_statement=waf.CfnWebACL.ByteMatchStatementProperty(
                    search_string='/admin',
                    field_to_match=waf.CfnWebACL.FieldToMatchProperty(uri_path={}),
                    positional_constraint="EXACTLY",
                    text_transformations=[waf.CfnWebACL.TextTransformationProperty(
                        priority=0,
                        type="NONE"
                    )
                    ],
                )
            ),
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                sampled_requests_enabled=True,
                metric_name='DemoSPACustomRuleMetric',
            )
        )
        # WebACL
        self.web_acl = waf.CfnWebACL(self, "DemoStaticWebsiteWebACL",
                                     default_action=waf.CfnWebACL.DefaultActionProperty(allow={}),
                                     scope='CLOUDFRONT',
                                     visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                                         cloud_watch_metrics_enabled=True,
                                         metric_name='DemoSPAWebACLMetric',
                                         sampled_requests_enabled=True
                                     ),
                                     name=f'DemoStaticWebsiteWebACL-1',
                                     rules=[
                                         custom_rule,
                                     ]
                                     )

        # OAI which gets attached to cloudfront distribution
        self.origin_access_identity = cloudfront.OriginAccessIdentity(self,
                                                                      "DemoStaticWebsiteOAI",
                                                                      comment="OAI for portal cloudfront distribution")
        # Cloudfront Distribution
        self.distribution = cloudfront.Distribution(self,
                                                    "DemoStaticWebsiteDistribution",
                                                    default_behavior=cloudfront.BehaviorOptions(
                                                        origin=origins.OriginGroup(
                                                            primary_origin=origins.S3Origin(self._host_bucket,
                                                                                            origin_access_identity=self.origin_access_identity),
                                                            fallback_origin=origins.HttpOrigin(
                                                                self._host_bucket.bucket_website_domain_name),
                                                            fallback_status_codes=[500]
                                                        ),
                                                        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                                                        # To accommodate CORS
                                                        allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                                                        cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                                                        origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN
                                                    ),
                                                    default_root_object=constants.indexDocument,
                                                    web_acl_id=self.web_acl.attr_arn
                                                    # Custom domain here
                                                    # domain_names=['custom_domain.com'],
                                                    # Certificate for custom domain below, assuming it exists in aws certificate manager
                                                    # the below will need an import aws_cdk.aws_certificatemanager as certificatemanager
                                                    # certificate=certificatemanager.Certificate.from_certificate_arn('pre-existing-certificate-arn')
                                                    )
