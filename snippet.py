#!/usr/bin/env python3

# VMware SD-WAN GCP Deployment Manager - Create YAML & Deploy (20201208)
# Script to collect needful for VMware SD-WAN vEdge deployment and activation in Google Cloud Platform (GCP)
# IMPORTANT: Virtual Edge should already be configured in the VCO before running script - see GCP deployment guide
# NOTICE: This script requires authentication for GCLOUD CLI access
# Overview of GCLOUD CLI can be found here: https://cloud.google.com/sdk/gcloud/
# VMware does not guarantee the samples; they are provided "AS IS".

# Usage : ./vmware_sdwan_gcp_dm.py
# Logging: tail -f vmware_sdwan_gcp_dm.log

import logging
import sys
import yaml
import os
import pyinputplus as pyip

COMPUTE_URL_BASE = 'https://www.googleapis.com/compute/v1/'
user_input = {}


def generate_config(context):
    resources = {'resources':
                     [{'type': 'compute.v1.instance',
                       'name': context['velo_edge_name'],
                       'properties': {
                           'zone': 'us-west1-a',
                           'machineType': ''.join([COMPUTE_URL_BASE, 'projects/',
                                                   context['gcp_project_id'], '/zones/',
                                                   context['gcp_zone'], '/machineTypes/',
                                                   context['gcp_machine_type']]),
                           'canIpForward': True,
                           'disks': [{
                               'deviceName': 'boot',
                               'type': 'PERSISTENT',
                               'boot': True,
                               'autoDelete': True,
                               'initializeParams':
                                   {
                                       'sourceImage':
                                           ''.join([COMPUTE_URL_BASE,
                                                    'projects/vmware-sdwan-public/global/images/vce-342-102-r342'
                                                    '-20200610-ga-3f5ad3b9e2'])
                                   }
                           }],
                           'networkInterfaces': [
                               {'network': ''.join([COMPUTE_URL_BASE, 'projects/', context['gcp_project_id'],
                                                    '/global/networks/', context['mgmt_vpc']]),
                                'subnetwork': ''.join(['projects/', context['gcp_project_id'],
                                                       '/regions/', context['gcp_region'],
                                                       '/subnetworks/', context['mgmt_vpc_sn']])},
                               {'network': ''.join([COMPUTE_URL_BASE, 'projects/', context['gcp_project_id'],
                                                    '/global/networks/', context['public_vpc']]),
                                'subnetwork': ''.join(['projects/', context['gcp_project_id'],
                                                       '/regions/', context['gcp_region'],
                                                       '/subnetworks/', context['public_vpc_sn']]),
                                'accessConfigs': [{'name': 'External NAT', 'type': 'ONE_TO_ONE_NAT'}]},
                               {'network': ''.join([COMPUTE_URL_BASE, 'projects/', context['gcp_project_id'],
                                                    '/global/networks/', context['private_vpc']]),
                                'subnetwork': ''.join(['projects/', context['gcp_project_id'],
                                                       '/regions/', context['gcp_region'],
                                                       '/subnetworks/', context['private_vpc_sn']])}
                           ],
                           'metadata': {
                               'items': [
                                   {'key': 'user-data',
                                    'value': '#cloud-config\nvelocloud:\n vce:\n  vco: ' + context['velo_vco']
                                             + '\n  activation_code: ' + context['velo_key']
                                             + '\n  vco_ignore_cert_errors: ' + context['velo_cert_err'] + '\n'
                                    }]}
                       }
                       }]
                 }

    configuration = yaml.dump(resources)

    logging.info('========================yaml.dump=============================')
    logging.info(configuration)

    ack_results = pyip.inputYesNo("Does the above YAML look correct (yes or no)? ")
    if ack_results.lower() == "no" or ack_results.lower() == "n":
        logging.info('User declined YAML configuration')
        exit()
    if ack_results.lower() == "yes" or ack_results.lower() == "y":
        filename = context['velo_edge_name'] + '.yaml'
        yaml_file = open(filename, 'w')
        yaml_file.write(configuration)
        yaml_file.close()

        command = '/usr/bin/gcloud deployment-manager deployments create ' \
                  + context['velo_edge_name'] + ' --config ' + filename
        logging.info('Executing Deployment Manager...')
        logging.info(command)
        os.system(command)
    else:
        logging.error('Unknown acknowledgement received')
        exit()

    return


class StreamToLogger(object):
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def main():
    logging.basicConfig(filename='vmware_sdwan_gcp_dm.log', level=logging.INFO,
                        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    stdout_logger = logging.getLogger('STDOUT')
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl

    stderr_logger = logging.getLogger('STDERR')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl

    logging.info('New deployment started...')

    user_input["gcp_project_id"] = input("GCP Project ID: ")
    user_input["gcp_region"] = input("GCP Region (i.e. us-west1): ")
    user_input["gcp_zone"] = input("GCP Zone (i.e. us-west1-a): ")
    user_input["gcp_machine_type"] = input("GCP Machine Type (i.e. n1-standard-4): ")
    user_input["velo_edge_name"] = input("Velocloud Edge Name (lower-case only): ")
    user_input["velo_vco"] = input("Velocloud Orchestrator (FQDN or IP): ")
    user_input["velo_key"] = input("Velocloud Edge Activation Key: ")
    user_input["velo_cert_err"] = input("Ignore Certificate Errors (true or false): ")
    user_input["mgmt_vpc"] = input("Management VPC: ")
    user_input["mgmt_vpc_sn"] = input("Management VPC Subnet: ")
    user_input["public_vpc"] = input("Public (WAN) VPC: ")
    user_input["public_vpc_sn"] = input("Public VPC Subnet: ")
    user_input["private_vpc"] = input("Private (LAN) VPC: ")
    user_input["private_vpc_sn"] = input("Private VPC Subnet: ")

    logging.info('========================User Input=============================')
    logging.info(user_input)
    generate_config(user_input)

    exit()


if __name__ == '__main__':
    main()
