#!/usr/bin/env python
import argparse
import base64

import boto3
import docker


def _check_logs(logs, operation: str) -> None:
    for entry in logs:
        if "error" in entry:
            raise RuntimeError(f"Docker {operation} failed: {entry['error']}")


def create(repository_name: str, build_context: str, image_tag: str) -> None:
    ecr = boto3.client("ecr")
    repository_created = False

    try:
        repository = ecr.create_repository(repositoryName=repository_name)["repository"]
        repository_created = True
        image = f"{repository['repositoryUri']}:{image_tag}"

        docker_client = docker.from_env()
        build_logs = docker_client.images.build(path=build_context, tag=image, rm=True)[1]
        _check_logs(build_logs, "image build")

        authorization = ecr.get_authorization_token()["authorizationData"][0]
        username, password = base64.b64decode(authorization["authorizationToken"]).decode("utf-8").split(":", 1)

        push_logs = docker_client.images.push(
            repository["repositoryUri"],
            tag=image_tag,
            auth_config={"username": username, "password": password},
            stream=True,
            decode=True,
        )
        _check_logs(push_logs, "image push")
    except Exception:
        if repository_created:
            ecr.delete_repository(repositoryName=repository_name, force=True)
        raise

    print(image)


def delete(repository_name: str, image: str) -> None:
    boto3.client("ecr").delete_repository(repositoryName=repository_name, force=True)
    docker.from_env().images.remove(image, force=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("repository_name")
    create_parser.add_argument("build_context")
    create_parser.add_argument("image_tag")

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("repository_name")
    delete_parser.add_argument("image")

    args = parser.parse_args()
    if args.action == "create":
        create(args.repository_name, args.build_context, args.image_tag)
    else:
        delete(args.repository_name, args.image)


if __name__ == "__main__":
    main()
