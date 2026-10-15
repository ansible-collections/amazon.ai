# SageMaker training-job integration target

The target creates and removes its own S3 bucket and input file, ECR repository and training image,
IAM execution role, policy, and SageMaker training jobs. It builds the image with Docker and pushes
it to ECR. The integration runner therefore needs a working Docker daemon and AWS credentials with
permissions to manage these temporary resources and pass the execution role to SageMaker.

The instance type defaults to `ml.m5.large` and can be overridden with
`SAGEMAKER_TEST_INSTANCE_TYPE`. The AWS account and Region must allow that training instance type
and have SageMaker training quota available.

This target is billable. It starts multiple training jobs, including one that runs until stopped,
and creates a managed warm pool to test an in-place update. Training instances and warm-pool
capacity incur charges while they run. The training image is based on `python:3.12-slim`; the test
container writes a tiny model artifact and sleeps only for the stop test.
