import os
import time


def main() -> None:
    time.sleep(int(os.environ.get("SAGEMAKER_TEST_SLEEP_SECONDS", "0")))

    os.makedirs("/opt/ml/model", exist_ok=True)
    with open("/opt/ml/model/model.txt", "w", encoding="utf-8") as model_file:
        model_file.write("integration test model\n")


if __name__ == "__main__":
    main()
