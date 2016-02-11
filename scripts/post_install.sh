pip install -e ${INSTALLDIR}/${NAME}/

django-admin.py migrate --noinput --settings=heatherr.settings
django-admin.py collectstatic --noinput --settings=heatherr.settings
