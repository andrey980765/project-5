#  PhotoWeb Django Project

Проект представляет собой Django веб-приложение для загрузки изображений и хранения EXIF-метаданных.  
Поддерживает запуск как локально, так и в Docker (Windows/Linux).

---

##  Возможности

- Загрузка и хранение изображений
- Автоматический сбор EXIF-данных
- Django Admin интерфейс
- PostgreSQL база данных
- Автоматический запуск миграций и сбор статики при старте Docker
- Gunicorn для продакшн-сервера

---

##  Технологии

| Компонент | Версия |
|----------|--------|
| Python | 3.13 |
| Django | 5.x |
| PostgreSQL | 15 |
| Docker + Docker Compose | ✔ |
| Gunicorn | ✔ |

---

## Установка

Перед запуском убедитесь, что установлены:

### Windows
- Docker Desktop → https://www.docker.com/products/docker-desktop  
(Compose уже включён)

### Linux (Ubuntu)
```sh
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable --now docker

Проверьте:
docker --version
docker-compose --version

Настройка .env
Создайте файл .env в корне проекта:
POSTGRES_DB=photodb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db

DJANGO_SECRET_KEY=super_secret_key
DJANGO_DEBUG=1

Запуск проекта:
1. Запуск через Docker.

Windows PowerShell:
docker-compose up --build

Linux:
docker-compose up --build

После первого запуска можно использовать:
docker-compose up

Приложение будет доступно: 
http://localhost:8000

Полезные команды:
docker-compose up -d	                                            Запуск в фоне
docker-compose down	                                                Остановить контейнеры
docker-compose logs -f web	                                        Лог сервера
docker-compose exec web python manage.py migrate	                Запуск миграций вручную
docker-compose exec web python manage.py collectstatic --noinput    Сбор статических файлов