# Kova Server — production container image.
#
# Simple single-stage build so it works anywhere Docker is available.
#
#   Build:  docker build -t kova-server .
#   Run  :  docker run --rm -p 5000:5000 \
#             -e KOVA_MONGO_URI="mongodb://localhost:27017/kova" \
#             -e KOVA_JWT_SECRET="change-me-to-a-long-random-string" \
#             kova-server
#
# Note: the server needs a reachable MongoDB at boot (fails fast after 5s),
# and in production it refuses to start unless KOVA_JWT_SECRET is set.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000 \
    KOVA_ENV=production \
    FLASK_ENV=production

WORKDIR /app

# Dependencies first — this layer is cached until requirements.txt changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code + avatar assets + entrypoint.
COPY app ./app
COPY run.py ./

EXPOSE 5000

# run.py --production serves the API with Waitress on 0.0.0.0:$PORT.
CMD ["python", "run.py", "--production"]
