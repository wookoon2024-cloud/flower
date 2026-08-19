# 🌿 데스크톱 플로팅 AI 반려화분 위젯 (GovAI Companion Plant)

> **범정부 AI 공통기반(dev.ai.go.kr) API 연동 업무망 힐링 다마고치 위젯**

---

## 🌟 주요 특징
1. **투명 플로팅 UI (`PySide6`):**
   - 창 테두리 없는 투명 배경 (`FramelessWindowHint`, `WA_TranslucentBackground`)
   - 항상 화면 최상위 상주 (`WindowStaysOnTopHint`)
   - 자유로운 마우스 드래그 이동 및 우클릭 컨텍스트 메뉴 지원
2. **로컬 다마고치 육성 엔진:**
   - 수분(`water`), 햇빛(`sunlight`), 애정도(`affection`), 4단계 성장(`stage 1~4`)
   - 오프라인 부재 시간 자동 계산 및 자연 감쇠(Decay) 반영
   - 수분/햇빛 부족 시 긴급 말풍선 알림
3. **로컬 SQLite3 영속화 & 슬라이딩 윈도우:**
   - 대화 내역 영속화 및 API 호출 시 최근 4~6건(2~3턴) 컨텍스트 윈도우 자동 추출
4. **범정부 AI API (`dev.ai.go.kr`) & QThread 비동기 워커:**
   - 메인 스레드 프리징 없는 비동기 통신
   - 5초 타임아웃 및 업무망 폐쇄망용 Fallback 로컬 인텔리전트 대사 시스템
   - 사설 인증서/망분리 환경을 위한 SSL 검증 우회 옵션
5. **독립 배포 바이너리:**
   - PyInstaller 기반 단일 실행 파일 (`dist/AICompanionPlant.exe`) 지원

---

## 📁 디렉터리 구조
```text
멀티클립보드/
├── ai_plant/
│   ├── __init__.py
│   ├── config.py              # 설정 파일 로더 및 경로 유틸
│   ├── database.py            # SQLite3 DB 매니저 및 슬라이딩 윈도우
│   ├── plant_engine.py        # 다마고치 육성/감쇠/진화 엔진
│   ├── ai_client.py           # QThread 비동기 API 통신 및 Fallback
│   └── ui/
│       ├── __init__.py
│       ├── floating_widget.py # 메인 투명 플로팅 윈도우
│       ├── bubble_widget.py   # 가변형 말풍선 위젯
│       ├── character_widget.py# 화분 캐릭터 스프라이트 & 파티클 애니메이션
│       ├── control_bar.py     # 하단 상태 게이지 및 버튼바
│       ├── chat_dialog.py     # 대화 팝업창
│       └── settings_dialog.py # 환경 설정 대화상자
├── assets/                    # 화분 단계별 PNG 및 아이콘 리소스
├── config.json                # API 및 위젯 설정 파일
├── main.py                    # 프로그램 진입점
├── build_exe.py               # PyInstaller 빌드 자동화 스크립트
├── build_exe.bat              # 윈도우 간편 빌드 배치 파일
├── test_suite.py              # 단위/통합 테스트 스위트
├── INSTALL_GUIDE.md           # 상세 설치 및 설정 가이드
└── README.md                  # 프로젝트 설명서
```

---

## 🚀 빠른 시작 (개발 환경)
```bash
# 1. 의존성 패키지 확인
pip install PySide6 requests pillow pyinstaller

# 2. 그래픽 리소스 생성
python generate_assets.py

# 3. 단위 테스트 실행
python test_suite.py

# 4. 프로그램 실행
python main.py

# 5. 독립 실행 파일(.exe) 빌드
python build_exe.py
# 또는 build_exe.bat 더블클릭
```

---

## 📄 라이선스
MIT License
