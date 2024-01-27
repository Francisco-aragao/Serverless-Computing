FROM python:3.9-slim

# Separate folder for this application
WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

# Make sure we can port forward to this later
EXPOSE 32182

# Using streamlit to handle dashboard graphics (will redirect matplotlib data and other stuff)
ENTRYPOINT ["streamlit", "run", "dashboard.py", "--server.port=32182", "--server.address=0.0.0.0"] 