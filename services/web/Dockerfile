FROM python:3.12-slim

WORKDIR /app

RUN useradd -m appuser

COPY services/web/pyproject.toml ./
RUN touch README.md

RUN pip install --no-cache-dir streamlit redis plotly pydantic-settings Pillow

COPY services/web/ ./

RUN chown -R appuser:appuser /app
USER appuser

ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]