FROM python:3.11-slim

RUN useradd -m -u 1000 user
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir --no-deps -e . \
    # repo files can arrive mode 600/700; the runtime user must read assets/tokens/fonts
    && chmod -R a+rX /app

USER user
ENV HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    # The Space IS the hosted demo: judge-only presets, API backends, recorded seeds.
    # Space variables (Settings -> Variables) override these at runtime.
    SIRIN_UI_HOSTED=1 \
    SIRIN_OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free \
    STREAMLIT_SERVER_MAX_UPLOAD_SIZE=5
EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "sirin/ui/streamlit_app.py", \
  "--server.port=8501", "--server.address=0.0.0.0", \
  "--server.headless=true", "--server.enableXsrfProtection=false"]
