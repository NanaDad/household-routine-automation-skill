#!/usr/bin/env bash
# macOS(Apple Silicon/Intel) 설치: bash install.sh
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; cd "$D"
command -v python3 >/dev/null || { echo "python3 필요: brew install python@3.12"; exit 1; }
# insightface는 C 확장 빌드가 필요 → Xcode CLT 확인
if [[ "$(uname)" == "Darwin" ]] && ! xcode-select -p >/dev/null 2>&1; then
  echo "Xcode Command Line Tools 설치 필요: xcode-select --install 실행 후 다시 시도"; exit 1; fi
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip wheel setuptools Cython
.venv/bin/pip install -q -r requirements.txt
chmod +x kidface.sh
# 모델(buffalo_l, ~280MB) 1회 다운로드 → ~/.insightface/models. 이후 완전 오프라인.
.venv/bin/python -c "import sys; sys.path.insert(0,'kidface'); import cli; cli.get_app()" >/dev/null 2>&1
echo "설치 완료. 사용: $D/kidface.sh --help"
