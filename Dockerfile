FROM python:3.12-slim
RUN pip install --no-cache-dir uv==0.12.17
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
# data/ is not in the image; fetched on first start (public UCI datasets)
CMD ["sh", "-c", "uv run --no-dev python scripts/download_data.py && uv run --no-dev streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
EXPOSE 8501
