# Implement enough runner using AI to make the simple_country_test pass

## Problem

We have generated a plan and steps that run a simple conversation with an AI, checking the answers.

The test runner script is

.\run_test_plan.ps1 -Clean -y -PlanFile .\overview_simple_run_test_country_aiwhisperer_config.json -Config .\aiwhisperer_config.yaml -OutputProjectFolder . -AIWhispererRootPath ..\..\

from tests\simple_run_test_county folder

with the original requirements being the project_dev\rfc\simple_run_test_country.md

Most of the functionality except the actual processing of each step is already done and integrated into the code base.
The initial plan should carefully examine what exists already AND only implement parts that don't exist already

## Goal

At the moment the runner doesn't do anything except log each task was successfully, we need to implement enough functionality for the country test to complete without cheating using a real AI over a real openrouter connections.

This should include an expensive and slow integration test (only run on demand) allowing us to test for regression later on.
