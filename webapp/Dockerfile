FROM python:3.13.2-slim

WORKDIR /opt/flask

RUN pip install flask==3.1.2 gunicorn==23.0.0 uvicorn==0.37.0

# COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
