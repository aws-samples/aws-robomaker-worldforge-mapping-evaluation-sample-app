#!/usr/bin/env python

"""
This script is purely to help create the 'batch_config.json' file to launch batch simulation parameters for
sample application at https://github.com/aws-samples/aws-robomaker-worldforge-mapping-evaluation-sample-app.

The parameters in this template are not exhaustive, and may not apply to all applications.
Users should refer the following two api's
https://docs.aws.amazon.com/robomaker/latest/dg/API_CreateSimulationJob.html
https://docs.aws.amazon.com/robomaker/latest/dg/API_StartSimulationJobBatch.html
to expand to other applications.

usage: 'python create_batch_params.py'
"""


import json

### Fill these values before running the script
list_of_world_arns = []
subnet_1 = ""
subnet_2 = ""
security_group = ""
assign_ip = True
iam_arn = ""
sim_app_arn = ""
bucket_name=""
### Stop filling here
sim_job_requests = []
config= {}
config['batchPolicy'] = { "timeoutInSeconds": 7200, "maxConcurrency": 5 }

def job_params(IAM_ARN, SIM_APP_ARN, WORLD_ID="", BUCKET_NAME="", SUBNET_1="", SUBNET_2="", SECURITY_GROUP="", ASSIGN_IP=True):
    return {
        "maxJobDurationInSeconds": 3600,
        "iamRole": IAM_ARN,
        "failureBehavior": "Fail",
        "simulationApplications": [
            {
                "application": SIM_APP_ARN,
                "launchConfig": {
                    "packageName": "simulation_app",
                    "launchFile": "mapping_sample_application.launch",
                    "environmentVariables": {
                        "TURTLEBOT3_MODEL": "waffle_pi",
                        "BUCKET_NAME": BUCKET_NAME,
                        "GAZEBO_WORLD": WORLDFORGE,
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

for world_id in list_of_world_arns:
    sim_job_requests.append(job_params(iam_arn, sim_app_arn, world_id, bucket_name, subnet_1, subnet_2, security_group, assign_ip))

config['createSimulationJobRequests'] = sim_job_requests
with open("batch_config.json", 'w') as f:
    f.write(json.dumps(config,indent=4, sort_keys=True ))
