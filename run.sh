#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "❌ 가상환경이 없습니다. 먼저 ./install.sh 를 실행하세요."
    exit 1
fi

source venv/bin/activate
python app.py
