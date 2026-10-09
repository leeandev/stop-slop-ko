#!/bin/sh
# 쓸 수 있는 파이썬을 골라 문서 라우팅 훅을 실행한다(macOS/Linux=python3, Windows=python).
# 파이썬이 없으면 아무것도 주입하지 않고 끝낸다.
dir=$(dirname "$0")
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "import sys" </dev/null >/dev/null 2>&1; then
    exec "$py" "$dir/stop-slop-doc-reminder.py"
  fi
done
exit 0
