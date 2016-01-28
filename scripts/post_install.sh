pip install -e .

django-admin.py migrate --noinput --settings=heatherr.settings
django-admin.py collecstatic --noinput --settings=heatherr.settings
