# Yatube
## Описание:
Cоциальную сеть. Она даёт пользователям возможность создать учетную запись, публиковать записи, подписываться на любимых авторов и отмечать понравившиеся записи. Используется кэширование и пагинация. Регистрация реализована с верификацией данных, сменой и восстановлением пароля через почту. Модерация записей, работа с пользователями, создание групп осуществляется через панель администратора. Написаны тесты проверяющие работу сервиса.

## Технологии:
- Python 3.7
- Django 2.2.16
- Unittest

## Как запустить проект:
1. Клонировать репозиторий и перейти в него в командной строке:
```
git@github.com:Hello09Andrey/hw05_final.git
```
2. Перейти в рабочий каталог:
```
cd hw05_final/
```
3. Cоздать и активировать виртуальное окружение(Windows):
```
python -m venv venv
```
```
source venv/Scripts/activate
```
4. Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
5. В директории проекта создайте файл .env и добавьте, необходимые данные для запуска проекта:
```
EMAIL_HOST_USER = 'имя пользователя для аутентификации на SMTP-сервере'
EMAIL_HOST_PASSWORD = 'пароль для аутентификации на SMTP-сервере'
DEFAULT_FROM_EMAIL = 'адрес электронной почты отправителя'
```
6. Выполните миграции:
```
python manage.py migrate
```
7. Для создания суперпользователя выполните команду:
```
python manage.py createsuperuser
```
8. В папке с файлом manage.py выполните команду:
```
python manage.py runserver
```
Проект запустится на http://127.0.0.1:8000/.

Для подтверждения регистрации и сброса пароля используйте папку sent_emails

## Автор:
- Белоусов Андрей