FROM supervisely/base-py-sdk:6.73.378

RUN pip install git+https://github.com/supervisely/supervisely.git@branch-for-anomaly-sorter
RUN pip install apscheduler==3.11.0

LABEL python_sdk_version=6.73.378
