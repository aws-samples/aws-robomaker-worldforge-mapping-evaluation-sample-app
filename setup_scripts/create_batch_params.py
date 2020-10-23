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
import os
import sys


def job_params( WORLD_ID ):
    SUBNET_1 = os.environ['SUBNET_1']
    SUBNET_2 = os.environ['SUBNET_2']
    SECURITY_GROUP = os.environ['SECURITY_GROUP']
    IAM_ARN = os.environ['IAM_ROLE_ARN']
    SIM_APP_ARN = os.environ['SIM_APP_ARN']
    BUCKET_NAME = os.environ['BUCKET_NAME']
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
                        "GAZEBO_WORLD": "WORLDFORGE",
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
            "assignPublicIp": True
        },
    }


if __name__ == "__main__":
    sim_job_requests = []
    config= {}
    config['batchPolicy'] = { "timeoutInSeconds": 7200, "maxConcurrency": 5 }
    
    with open('generation_job_output.json', 'r') as f:
        output_world_generation = json.load(f)

    list_of_world_arns = output_world_generation['finishedWorldsSummary']['succeededWorlds']

    for world_id in list_of_world_arns:
        sim_job_requests.append(job_params(world_id))

    config['createSimulationJobRequests'] = sim_job_requests
    with open("batch_config.json", 'w') as f:
        f.write(json.dumps(config,indent=4, sort_keys=True ))
    print("Completed writing batch configuration to batch_config.json")