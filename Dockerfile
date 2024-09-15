##############################################################
# Install Package. Root user
##############################################################
FROM apache/airflow  AS airflow-base
USER root
RUN apt-get update && apt-get install -y \
    libpq-dev

##############################################################
# Install Libs. Airflow user
##############################################################
FROM airflow-base
# ARG PYPI=$PYPI
USER airflow

# COPY --chown=airflow:root _dags /opt/airflow/_dags  ##  отключаем деплой дагов вместе с образом airflow. Даги деплоятся отдельными задачами из infra
COPY requirements.txt \
     /opt/airflow/
RUN pip install  -r ./requirements.txt
