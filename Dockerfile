FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# демо-сайты: custom/ + demos/*.yaml → site/demo/
RUN python build.py >/dev/null && useradd -r -u 10001 otto && mkdir -p /app/data && chown otto /app/data
ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA
USER otto
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "--access-logfile", "-", "wsgi:app"]
