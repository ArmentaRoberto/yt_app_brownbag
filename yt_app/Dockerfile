FROM python:3.11-slim
WORKDIR /app
COPY . /app
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y gettext vim
RUN pip install --no-cache-dir -r /app/requirements.txt
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/wait-for-it.sh
RUN chmod +x /usr/wait-for-it.sh
COPY replace-placeholders.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/replace-placeholders.sh
ENTRYPOINT ["/usr/local/bin/replace-placeholders.sh", "/usr/wait-for-it.sh", "db:5432", "--"]
EXPOSE 5010
CMD ["ddtrace-run", "python", "main.py"]