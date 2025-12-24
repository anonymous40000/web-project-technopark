# gunicorn -c olegoverflow.conf.py olegoverflow_wsgi:app - так я запускаю

bind = "127.0.0.1:9091"
workers = 2
proc_name = "olegoverflow"
