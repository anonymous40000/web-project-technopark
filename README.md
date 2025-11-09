# OlegOverFlow

Клон Stack Overflow, созданный на Django в учебных целях.

## Возможности (пока реализованы не все)

- Система вопросов и ответов
- Фильтрация вопросов по тегам
- Аутентификация пользователей (вход, регистрация)
- Постраничное отображение
- Система голосования

## Страницы

- `/` - Новые вопросы
- `/hot/` - Популярные вопросы (сортировка по голосам)
- `/questions/tag/<tag_name>/` - Вопросы по тегу
- `/questions/<id>/` - Страница вопроса с ответами
- `/auth/ask/` - Задать новый вопрос
- `/auth/login/` - Страница входа
- `/auth/register/` - Страница регистрации

## Технологии

- **Бэкенд**: Django 5.2
- **Фронтенд**: HTML, CSS, JavaScript
- **База данных**: SQLite (разработка)
- **Ссылка на проектирование моделей данных**: https://dbdocs.io/eurser/designing-database-models?table=UserProfile&schema=public&view=table_structure (включать надо с VPN)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/anonymous40000/web-project-technopark.git
```
2. Перейдите в папку проекта:
```bash
cd web-project-technopark
```
3. Создайте виртуальное окружение:
```bash
python -m venv venv
```
4. Активируйте виртуальное окружение:
```bash
source venv/bin/activate
```
5. Установите зависимости:
```bash
pip install -r requirements.txt
```
6. Запустите сервер:
```bash
python manage.py runserver
```
