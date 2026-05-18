# Reels Downloader

인스타그램 Reels를 로컬 웹 UI에서 일괄 다운로드하는 도구. 1080p H.264 + AAC 형식으로 저장하며, macOS QuickTime에서 바로 재생 가능.

## 기능

- 여러 개의 Reels URL을 한 번에 다운로드 (텍스트에 섞여 있어도 자동 추출)
- 1080p 우선 다운로드 (Instagram이 VP9로만 제공하는 경우 자동으로 H.264 재인코딩)
- 진행 상태 실시간 표시 (다운로드 / 변환 / 완료)
- 로그인 필요 콘텐츠는 브라우저 쿠키 사용 (Chrome / Safari / Firefox / Edge / Brave)

## 요구사항

- macOS (Linux도 가능하나 미테스트)
- Python 3.9+
- ffmpeg
- Homebrew (ffmpeg 자동 설치용, 없으면 수동 설치)

## 설치

```bash
git clone https://github.com/ININ-NINI/reels-downloader.git
cd reels-downloader
./install.sh
```

`install.sh`가 자동으로:
1. ffmpeg 설치 확인 (없으면 brew로 설치)
2. Python venv 생성
3. Flask + yt-dlp 설치

## 사용

```bash
./run.sh
```

브라우저에서 http://127.0.0.1:5000 접속.

1. 인스타그램 Reels URL을 줄바꿈으로 여러 개 입력
2. (선택) 쿠키 사용할 브라우저 선택 — 비공개/연령제한 콘텐츠용
3. **다운로드** 클릭
4. `~/Downloads/Reels/` 폴더에 저장됨

## 파일명 규칙

```
{업로더}_{영상ID}.mp4
예: Charles Lopez_DXW7m9rioQv.mp4
```

## 트러블슈팅

**`This content isn't available to everyone` 에러**
→ UI에서 본인이 인스타그램에 로그인된 브라우저를 선택. Chrome 권장.

**Chrome 쿠키 사용 시 키체인 비밀번호 입력 프롬프트가 뜸**
→ macOS 로그인 비밀번호 입력. Chrome Safe Storage 접근에 필요.

**영상이 macOS에서 재생 안 됨**
→ 정상 동작. 자동으로 H.264로 재인코딩되므로 결과물은 QuickTime에서 재생됨.

**저장 위치를 바꾸고 싶음**
→ `app.py`의 `DOWNLOAD_DIR` 변수 수정.

## 기술 스택

- Flask (로컬 웹서버, 단일 사용자용)
- yt-dlp (Instagram 메타데이터/스트림 추출)
- ffmpeg (VP9 → H.264 재인코딩)
- Vanilla JS (Streaming NDJSON으로 진행 상태 표시)
