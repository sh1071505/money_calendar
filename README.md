# 가계 달력

달력 중심의 자산·수입·지출 관리 웹앱 (아이폰 홈 화면 앱으로 사용).

- `index.html` 앱 본체. 기록 데이터는 기기 안(localStorage)에만 저장되고 이 저장소에는 올라가지 않아요.
- `data/watchlist.json` 자동 시세를 받을 해외주식 티커와 코인 심볼. 종목을 새로 사면 여기에 추가하세요.
- `data/prices.json` 매일 06:40(KST) GitHub Actions가 갱신 (해외주식: Yahoo → Stooq, 코인: 업비트, 환율).
- `reports/` 매월 1일 Claude 예약 작업이 지난달 경제 리포트를 올려요. 형식은 `reports/REPORT_SPEC.md`.

## 처음 설정
1. Settings → Pages → Branch `main` / `(root)` 저장 → `https://sh1071505.github.io/money_calendar/`
2. Settings → Actions → General → Workflow permissions → Read and write
3. Actions 탭 → "시세 갱신" → Run workflow (첫 시세 생성)
4. 아이폰 사파리로 주소 열기 → 공유 → 홈 화면에 추가
