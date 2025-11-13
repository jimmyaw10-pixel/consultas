# Usa una imagen de PHP que viene con el servidor web Caddy (más simple que Apache)
FROM dunglas/frankenphp:latest-php8.2-alpine

# 1. Fuerza la instalación de los drivers MySQL (esto es esencial y usa 'apk' para Alpine)
RUN apk add --no-cache libpq-dev \
    && docker-php-ext-install pdo pdo_mysql

# 2. Copia tu código
COPY . /app
