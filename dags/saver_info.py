from datetime import timedelta, datetime


from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

from airflow.models import Variable
import json, requests

token =  Variable.get("token_api_openweathermap")
cityname = Variable.get("city_name")

def fetch_data(ti, **kwargs):



    response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={cityname}&lang=ru&units=metric&appid={token}")
    if response.status_code == 200:
        data_string = response.text

        order_data_dict = json.loads(data_string)

        new_d = {}

        new_d["max_temp"] = order_data_dict["main"]["temp_max"]
        new_d["min_temp"] = order_data_dict["main"]["temp_min"]
        new_d["description"] = order_data_dict["weather"][0]["description"]
        new_d["wind_speed"] = order_data_dict["wind"]["speed"]
        new_d["name"] = order_data_dict["name"]

        ti.xcom_push(key="name", value= new_d["name"])
        ti.xcom_push(key="max_temp", value= new_d["max_temp"])
        ti.xcom_push(key="min_temp", value= new_d["min_temp"])
        ti.xcom_push(key="wind_speed", value= new_d["wind_speed"])
        ti.xcom_push(key="description", value= new_d["description"])


default_args = {
    'owner': 'me',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='save_city_info_weather_v01',
    default_args=default_args,
    start_date=datetime(2024, 9, 14),
    tags=['saver'],
    schedule_interval='0 * * * *'
) as dag:
    task1_create_table = PostgresOperator(
        task_id='save_city_info_weather',
        postgres_conn_id='postgres_localhost',
        sql = """
            create table if not exists weathers (
                id serial PRIMARY KEY ,
                city_name VARCHAR,
                max_temp VARCHAR,
                min_temp VARCHAR,
                wind VARCHAR,
                descript VARCHAR
            )
        """
    )

    task2_fetcher_data = PythonOperator(
        task_id='fetcher_data',
        provide_context=True,
        python_callable=fetch_data,
        op_kwargs = {'token': token, 'cityname': cityname}
    )

    task3_insert_data = PostgresOperator(
        task_id='insert_data',
        postgres_conn_id='postgres_localhost',
        sql='''insert into weathers (city_name, max_temp, min_temp, wind, descript)
            values (
                     '{{ti.xcom_pull(task_ids="fetcher_data", key="name")}}',
                     '{{ti.xcom_pull(task_ids="fetcher_data", key="max_temp")}}',
                     '{{ti.xcom_pull(task_ids="fetcher_data", key="min_temp")}}',
                     '{{ti.xcom_pull(task_ids="fetcher_data", key="wind_speed")}}',
                     '{{ti.xcom_pull(task_ids="fetcher_data", key="description")}}'); ''',
        autocommit=True
    )

    task1_create_table >> task2_fetcher_data >> task3_insert_data
