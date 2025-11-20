# PhotoMetadata Manager

Веб-приложение на Django для загрузки, просмотра и редактирования метаданных фотографий из **JSON** файлов или **базы данных**.

---

##  Функционал
-  Загрузка JSON файлов с метаданными.
-  Просмотр и фильтрация данных из базы данных или JSON.
-  Редактирование записей через модальное окно с валидацией.
-  Удаление записей без перезагрузки страницы (AJAX).
-  Поиск по базе данных в реальном времени.

---

##  Установка

1. Клонировать репозиторий:
    git clone https://github.com/andrey980765/4-th_project.git
    cd photometadata
2. Создать виртуальное окружение:
    python -m venv venv
    venv\Scripts\activate   # для Windows
    source venv/bin/activate  # для Linux/Mac
3. Установить зависимости:
    pip install -r requirements.txt
4. Применить миграции:
    python manage.py migrate
5. Запустить локально:
    python manage.py runserver
