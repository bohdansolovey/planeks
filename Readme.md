# Test project 
## Рython 3.6
### How to build this project ? 
1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput`
4. in 1st terminal: `$ redis-server`
5. in 2nd terminal: `celery worker -A planekstest --loglevel=INFO --concurrency=2`
6. in 3rd terminal: `python manage.py runserver`

### About
- You can read docs of this api  when its running on address /docs

##### TODO: fix dockerfile (after fix problems with provider), add core/models folder
