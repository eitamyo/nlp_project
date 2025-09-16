FROM python:3.9-slim

WORKDIR /app
RUN pip install wikiextractor

COPY hewiki-latest-pages-articles.xml.bz2 /app/

CMD ["python", "-m", "wikiextractor.WikiExtractor", "--no-templates", "--json", "--output", "/app/output", "/app/hewiki-latest-pages-articles.xml.bz2"]