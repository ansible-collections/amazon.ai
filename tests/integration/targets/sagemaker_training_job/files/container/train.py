import os
import time


def main() -> None:
    time.sleep(int(os.environ.get("SAGEMAKER_TEST_SLEEP_SECONDS", "0")))


if __name__ == "__main__":
    main()
