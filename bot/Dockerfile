FROM python:3.12

WORKDIR /app
COPY . .
RUN apt-get update && apt-get install tesseract-ocr -y
RUN pip install -r requirements.txt

CMD ["python", "main.py"]