#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "📦 Reels Downloader 설치 시작"

# ffmpeg 체크
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg가 설치되어 있지 않습니다."
    if command -v brew &> /dev/null; then
        echo "→ Homebrew로 ffmpeg 설치 중..."
        brew install ffmpeg
    else
        echo "❌ Homebrew가 필요합니다."
        echo "   https://brew.sh 에서 설치 후 다시 실행하세요."
        echo "   또는 ffmpeg을 직접 설치하세요: https://ffmpeg.org/download.html"
        exit 1
    fi
else
    echo "✅ ffmpeg 확인됨"
fi

# Python 체크
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3가 필요합니다."
    exit 1
fi
echo "✅ Python $(python3 --version | awk '{print $2}') 확인됨"

# venv 생성
if [ ! -d venv ]; then
    echo "→ Python 가상환경 생성 중..."
    python3 -m venv venv
fi

# 의존성 설치
echo "→ Python 패키지 설치 중..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "✅ 설치 완료!"
echo "   실행:  ./run.sh"
echo "   접속:  http://127.0.0.1:5000"
echo "   저장:  ~/Downloads/Reels/"
