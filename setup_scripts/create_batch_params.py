#!/usr/bin/env python

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json

list_of_worlds = [
    ]

config= {}
config['batchPolicy'] = { "timeoutInSeconds": 7200, "maxConcurrency": 5 }
sim_job_requests = []
SUBNET_1 = ""
SUBNET_2 = ""
SECURITY_GROUP = ""
ASSIGN_IP = True
IAM_ARN = ""
SIM_APP_ARN = ""

def job_params(IAM_ARN, SIM_APP_ARN, WORLD_ID="", SUBNET_1="", SUBNET_2="", SECURITY_GROUP="", ASSIGN_IP=True):
    return {
        "maxJobDurationInSeconds": 3600,
        "iamRole": IAM_ARN,
        "failureBehavior": "Fail",
        "simulationApplications": [
            {
                "application": SIM_APP_ARN,
                "launchConfig": {
                    "packageName": "simulation_app",
                    "launchFile": "worldforge_turtlebot_navigation.launch",
                    "environmentVariables": {
                        "TURTLEBOT3_MODEL": "waffle_pi",
                        "BUCKET_NAME": "data-client",
                    },
                   "streamUI": True
                },
                "worldConfigs": [
                    {
                        "world": WORLD_ID
                    }
                ]
            }
        ],
        "vpcConfig": {
            "subnets": [
                SUBNET_1,
                SUBNET_2,
            ],
            "securityGroups": [
                SECURITY_GROUP
            ],
            "assignPublicIp": ASSIGN_IP
        },
    }

for WORLD_ID in list_of_worlds:
    sim_job_requests.append(job_params(IAM_ARN,SIM_APP_ARN, WORLD_ID, SUBNET_1, SUBNET_2, SECURITY_GROUP, ASSIGN_IP))
config['createSimulationJobRequests'] = sim_job_requests
with open("batch_config.json", 'a') as f:
    f.write(json.dumps(config,indent=4, sort_keys=True ))
