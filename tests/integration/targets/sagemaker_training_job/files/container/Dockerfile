FROM python:3.12-slim

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin sagemaker \
    && mkdir -p /opt/ml/code /opt/ml/model \
    && chown sagemaker:sagemaker /opt/ml/model

COPY --chown=root:root --chmod=0444 train.py /opt/ml/code/train.py

USER sagemaker
ENTRYPOINT ["python", "/opt/ml/code/train.py"]
