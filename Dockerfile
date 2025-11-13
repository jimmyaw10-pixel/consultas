# Usa una imagen base de PHP oficial con Apache
FROM php:8.2-apache

# 1. Fuerza la instalación de los drivers MySQL (Soluciona "could not find driver")
# Se utiliza el comando "apt-get install -y libpq-dev" para asegurar dependencias
RUN apt-get update && apt-get install -y libpq-dev \
    && docker-php-ext-install pdo pdo_mysql

# 2. Habilita la reescritura de URL 
RUN a2enmod rewrite

# 3. Copia todo tu código (index.php) al servidor web
COPY . /var/www/html/

# 4. Comando de inicio
CMD ["apache2-foreground"]
