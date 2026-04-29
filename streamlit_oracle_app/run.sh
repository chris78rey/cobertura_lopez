#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

export JAVA_TOOL_OPTIONS="-Doracle.jdbc.timezoneAsRegion=false -Duser.timezone=UTC"

source .venv/bin/activate

streamlit run app.py --server.address 0.0.0.0
