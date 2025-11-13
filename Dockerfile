# Usa una imagen base de PHP oficial con Apache
FROM php:8.2-apache

# 1. Instala las dependencias de MySQL
RUN docker-php-ext-install pdo pdo_mysql

# 2. Habilita la reescritura de URL (necesaria para muchos proyectos PHP)
RUN a2enmod rewrite

# 3. Copia el código de tu aplicación al servidor web
COPY . /var/www/html/

# 4. Asegúrate de que index.php sea el archivo principal
CMD ["apache2-foreground"]
