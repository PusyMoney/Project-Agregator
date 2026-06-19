# Project-Agregator

Приложение для агрегации и просмотра логов Apache.

## Требования
- Python 3.8+
- PostgreSQL
- Зависимости из `requirements.txt`

## Установка
1. Клонировать репозиторий
2. Создать виртуальное окружение: `python -m venv venv`
3. Активировать: `source venv/bin/activate` (Linux) или `venv\Scripts\activate` (Windows)
4. Установить зависимости: `pip install -r requirements.txt`
5. Настроить `config.json` (указать путь к логам и строку подключения БД)
6. Создать БД в PostgreSQL
7. Инициализировать миграции:  
   `flask db init`  
   `flask db migrate -m "init"`  
   `flask db upgrade`
8. Создать пользователя (можно через POST `/api/register` или вручную)
9. Запустить: `flask run`
10. Открыть `http://localhost:5000`

## Функции
- Авторизация
- Просмотр логов с фильтрацией (IP, дата, ключевое слово, URL, группировка)
- Статистика (всего записей, уникальных IP, URL)
- API для получения данных в JSON
- Парсинг логов (ручной и по расписанию, реализован через фоновые задачи)
- Отображение прогресса и списка обработанных файлов

## API Endpoints
- `POST /api/login` – вход
- `GET /api/logs` – получение логов с фильтрами
- `GET /api/stats` – статистика
- `GET /api/urls` – список URL с количеством
- `POST /api/parse` – запуск парсинга
- `GET /api/parse/status/<id>` – статус задачи
- `GET /api/parse/files` – список обработанных файлов
