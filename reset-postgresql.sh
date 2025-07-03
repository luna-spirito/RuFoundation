rm -rf postgresql
mkdir -p postgresql
initdb -D postgresql/data \
  --username=postgres \
  --encoding=UTF8 \
  --locale=en_US.UTF-8

pg_ctl -D postgresql/data -l postgresql/logfile start
sleep 1
createdb -U postgres scpwiki
python3 manage.py migrate
# psql -U postgres -d scpwiki -c "TRUNCATE TABLE django_content_type CASCADE;"
# psql -U postgres -d scpwiki -c "TRUNCATE TABLE web_user CASCADE;"
# psql -U postgres -d scpwiki -c "TRUNCATE TABLE web_tagscategory CASCADE;"
pg_ctl -D postgresql/data stop
