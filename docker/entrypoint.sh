#!/bin/sh
# Entry point of the agrotrust-metrics image.
#   serve   : simulate a fleet, build the HTML report and serve it on port 8000
#   anything else is passed to the agrometrics command line
set -e

if [ "$1" = "serve" ]; then
    NODES="${NODES:-14}"
    DAYS="${DAYS:-30}"
    SEED="${SEED:-42}"
    PORT="${PORT:-8000}"
    WORK="${WORK:-/tmp/agrotrust}"
    agrometrics simulate --nodes "$NODES" --days "$DAYS" --seed "$SEED" --out "$WORK/data"
    agrometrics report "$WORK/data/readings.csv" --events "$WORK/data/events.csv" --out "$WORK/site"
    echo "serving the report on port $PORT"
    exec python -m http.server "$PORT" --bind 0.0.0.0 --directory "$WORK/site"
fi

exec agrometrics "$@"
