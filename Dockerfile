FROM python:3.12
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./example.py /code/example.py
COPY ./pue /code/pue
CMD ["uvicorn", "example:APP", "--host", "0.0.0.0", "--port", "8080"]
