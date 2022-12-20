#!/bin/bash

set -ex

# Wait until Redpanda comes online
while [[ "$(curl -s redpanda:9644/v1/status/ready)" != "{\"status\":\"ready\"}" ]]; do sleep 5; done

pipenv run faust -A reddit_app worker -l info