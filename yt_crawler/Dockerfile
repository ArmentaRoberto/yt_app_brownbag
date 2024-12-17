FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y vim
RUN pip install -r requirements.txt
COPY . .
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/wait-for-it.sh
RUN chmod +x /usr/wait-for-it.sh
CMD ["/usr/wait-for-it.sh", "db:5432", "--strict", "--timeout=300", "--", "ddtrace-run", "python", "yt_crawler.py"]