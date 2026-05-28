FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /src

COPY requirements.txt /src/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /src/requirements.txt

COPY . /src

EXPOSE 8501

CMD ["streamlit", "run", "interface.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
