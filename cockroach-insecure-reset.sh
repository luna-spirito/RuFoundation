cockroach sql --insecure -e "
DROP DATABASE IF EXISTS scpwiki CASCADE;
DROP USER IF EXISTS scpwiki;
CREATE USER scpwiki;
CREATE DATABASE scpwiki OWNER scpwiki;
"
python3 manage.py migrate
python3 manage.py createsite -s backrooms -d localhost:8000 -t "Backrooms" -H "Backrooms"
echo "--- SUPERUSER: ---"
python3 manage.py createsuperuser
