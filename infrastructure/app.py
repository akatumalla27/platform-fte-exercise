#!/usr/bin/env python3
from aws_cdk import core as cdk
from spa.stack import SPAStack

app = cdk.App()
SPAStack(app, "spa")
app.synth()