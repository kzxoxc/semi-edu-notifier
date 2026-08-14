# edu-notifier

반도체 관련 교육 공고 3곳(한국반도체아카데미 / 반도체인프라활용현장인력양성 / 차세대반도체컨소시엄)을
매일 12:00, 18:00(KST)에 자동으로 확인해서 새 공고만 텔레그램으로 알려주는 봇.
GitHub Actions 위에서 돈다 — 내 PC를 켜둘 필요 없음.

## 1. 텔레그램 봇 만들기

1. 텔레그램에서 **@BotFather** 검색해서 대화 시작.
2. `/newbot` 입력 → 봇 이름, username 순서대로 물어보면 입력.
3. 완료되면 **토큰**(`1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` 형태)을 준다. 이게 `TELEGRAM_TOKEN`.
4. 만든 봇과 아무 대화나 한 번 해야 함 (예: `/start` 전송). 안 하면 5번에서 메시지 안 잡힘.

## 2. chat_id 알아내기

1. 브라우저에서 아래 주소 접속 (토큰 자리에 1번에서 받은 토큰 넣기):
   ```
   https://api.telegram.org/bot<여기에_토큰>/getUpdates
   ```
2. `"chat":{"id":123456789, ...}` 부분에서 숫자가 chat_id. 이게 `TELEGRAM_CHAT_ID`.
3. 결과가 비어있으면(`"result":[]`) 1-4번(봇과 대화 시작)을 안 한 것 — 다시 확인.

## 3. GitHub에 올리기

이 `edu-notifier` 폴더를 GitHub 레포로 만든다.

```bash
cd edu-notifier
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin <내_레포_주소>
git push -u origin main
```

## 4. GitHub Secrets 등록

레포 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

- `TELEGRAM_TOKEN` — 1번에서 받은 토큰
- `TELEGRAM_CHAT_ID` — 2번에서 받은 chat_id

## 5. 수동 테스트

레포 → **Actions** 탭 → **check** 워크플로 클릭 → **Run workflow** 버튼으로 수동 실행.
정상이면 새 공고 있을 때만 텔레그램 메시지 온다. (신규 없으면 조용히 끝남 — 정상 동작.)

이후로는 매일 12:00, 18:00(KST)에 자동 실행됨.

## 로컬에서 테스트하고 싶으면

```bash
pip install -r requirements.txt
export TELEGRAM_TOKEN=...
export TELEGRAM_CHAT_ID=...
python main.py
```

## 알아둘 점 (한계)

- **사이트 B(반도체인프라)**: robots.txt가 이 목록 페이지 크롤링을 막고 있는데, 사용자 확인 후 무시하고
  수집하는 중. 그리고 이 사이트는 상세페이지가 POST 요청 전용이라 텔레그램에 넣을 직접 링크가 없음 —
  대신 목록 페이지 링크를 보낸다. 클릭하면 목록에서 제목으로 찾아야 함.
- **사이트 A(반도체 아카데미)**: 재직자 대상(`lectTrgt: COMPANY`) 강의는 필터링해서 알림에서 뺀다.
  새로운 대상 구분값이 나타나면(현재 확인된 값: STUDENT/ALL/COMPANY 외의 값) 판단 안 하고 일단 알린다.
- 세 사이트 다 "신청시작"과 "마감"을 표시하는데, 사이트 C(공지사항 게시판)는 애초에 신청기간을
  구조화된 데이터로 안 주기 때문에 항상 "미기재"로 뜬다 — 정상.
- 한 사이트가 수집 0건이면 "파싱 결과 0건" 경고가 온다. 이건 사이트 구조가 바뀌어서 스크래퍼가
  깨졌다는 뜻일 가능성이 높음 — `scrapers/` 안의 해당 파일 점검 필요.
