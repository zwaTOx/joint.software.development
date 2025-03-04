FROM python:3.12.8

WORKDIR /app
COPY . .
RUN pip install -r req.txt

#http://localhost:1252/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]