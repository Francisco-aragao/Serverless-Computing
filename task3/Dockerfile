FROM python:3.9-slim-bullseye

# Same folder as usermodule in deployment.yaml from Task 1
# This ensures that runtime.py and usermodule.py are in the same folder
WORKDIR /opt

COPY . /opt

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "runtime.py"]