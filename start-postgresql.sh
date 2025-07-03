pg_ctl -D postgresql/data \
  -l postgresql/logfile \
  -o "-p 5432" \
  start
