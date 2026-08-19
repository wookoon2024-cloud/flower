"""
Settings Dialog Widget
Allows users to configure dev.ai.go.kr API endpoints, API Key, intranet SSL bypass,
plant names, decay rates, and perform reset actions.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QCheckBox, QSpinBox, QPushButton, QLabel, QGroupBox, QMessageBox, QTabWidget, QWidget,
    QComboBox, QApplication
)
from PySide6.QtCore import Qt, Signal

class SettingsDialog(QDialog):
    settings_saved = Signal()
    reset_plant_requested = Signal()
    clear_chat_requested = Signal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("⚙️ 반려화분 환경 설정")
        self.resize(460, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
                font-family: 'Malgun Gothic', 'Segoe UI';
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 14px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #0F766E;
            }
            QLineEdit, QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1.5px solid #10B981;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Tabs
        tabs = QTabWidget(self)

        # Tab 1: AI API Settings
        tab_api = QWidget()
        layout_api = QVBoxLayout(tab_api)
        layout_api.setSpacing(10)

        group_api = QGroupBox("범정부 AI / OpenAI / 로컬 LLM 연동 설정", tab_api)
        form_api = QFormLayout(group_api)
        form_api.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_api.setSpacing(8)

        # Provider Presets
        self.combo_preset = QComboBox(group_api)
        self.combo_preset.addItem("범정부 AI (dev.ai.go.kr)", "gov")
        self.combo_preset.addItem("OpenAI (api.openai.com)", "openai")
        self.combo_preset.addItem("로컬 Ollama (localhost:11434)", "ollama")
        self.combo_preset.addItem("로컬 LM Studio (localhost:1234)", "lmstudio")
        self.combo_preset.addItem("직접 입력 (Custom URL)", "custom")
        self.combo_preset.currentIndexChanged.connect(self.on_preset_changed)
        form_api.addRow("API 프리셋:", self.combo_preset)

        self.edit_endpoint = QLineEdit(group_api)
        self.edit_endpoint.setText(self.config.get("api_endpoint", "https://dev.ai.go.kr/api/v1/chat/completions"))
        self.edit_endpoint.setPlaceholderText("https://dev.ai.go.kr/api/v1/chat/completions")
        form_api.addRow("API 엔드포인트:", self.edit_endpoint)

        self.edit_apikey = QLineEdit(group_api)
        self.edit_apikey.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_apikey.setText(self.config.get("api_key", ""))
        self.edit_apikey.setPlaceholderText("발급받은 AI API Key 입력 (로컬은 생략 가능)")
        form_api.addRow("API Key:", self.edit_apikey)

        self.edit_model = QLineEdit(group_api)
        self.edit_model.setText(self.config.get("model", "gov-gpt-4o"))
        form_api.addRow("모델명 (Model):", self.edit_model)

        self.spin_timeout = QSpinBox(group_api)
        self.spin_timeout.setRange(2, 30)
        self.spin_timeout.setValue(self.config.get("timeout_sec", 5))
        self.spin_timeout.setSuffix(" 초")
        form_api.addRow("요청 타임아웃:", self.spin_timeout)

        self.chk_ssl = QCheckBox("SSL 인증서 검증 건너뛰기 (망분리/행정망 사설 인증서 대응)", group_api)
        self.chk_ssl.setChecked(not self.config.get("ssl_verify", False))
        form_api.addRow("", self.chk_ssl)

        # Connection Test Area
        test_row = QHBoxLayout()
        self.btn_test_api = QPushButton("⚡ API 연결 테스트", group_api)
        self.btn_test_api.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_api.setStyleSheet("""
            QPushButton {
                background-color: #EEF2FF;
                border: 1px solid #C7D2FE;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                color: #4338CA;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E0E7FF; }
        """)
        self.btn_test_api.clicked.connect(self.on_test_api_connection)
        self.lbl_test_result = QLabel("", group_api)
        self.lbl_test_result.setStyleSheet("font-size: 11px;")

        test_row.addWidget(self.btn_test_api)
        test_row.addWidget(self.lbl_test_result, 1)
        form_api.addRow("", test_row)

        layout_api.addWidget(group_api)
        layout_api.addStretch()
        tabs.addTab(tab_api, "🌐 AI API 설정")

        # Tab 2: Plant & Widget Settings
        tab_plant = QWidget()
        layout_plant = QVBoxLayout(tab_plant)
        layout_plant.setSpacing(10)

        group_profile = QGroupBox("화분 및 프로필 설정", tab_plant)
        form_profile = QFormLayout(group_profile)
        form_profile.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_profile.setSpacing(8)

        self.edit_plant_name = QLineEdit(group_profile)
        self.edit_plant_name.setText(self.config.get("plant_name", "초록이"))
        form_profile.addRow("화분 이름:", self.edit_plant_name)

        self.edit_user_name = QLineEdit(group_profile)
        self.edit_user_name.setText(self.config.get("user_nickname", "공직자님"))
        form_profile.addRow("사용자 호칭:", self.edit_user_name)

        self.chk_ontop = QCheckBox("항상 화면 최상위에 고정 (Always On Top)", group_profile)
        self.chk_ontop.setChecked(self.config.get("always_on_top", True))
        form_profile.addRow("", self.chk_ontop)

        self.chk_compact = QCheckBox("✨ 클릭 시 메뉴 표시 모드 (화분 클릭 시 메뉴 토글, 이동 시 화분만 표시)", group_profile)
        self.chk_compact.setChecked(self.config.get("compact_hover_mode", True))
        form_profile.addRow("", self.chk_compact)

        self.chk_ghost = QCheckBox("👻 고스트 반투명 모드 (평소 반투명, 마우스 올리면 선명화)", group_profile)
        self.chk_ghost.setChecked(self.config.get("ghost_mode", False))
        form_profile.addRow("", self.chk_ghost)

        self.chk_hourly = QCheckBox("⏰ 정시 리프레시 알림 (매 시 정각 스트레칭/시간대별 응원)", group_profile)
        self.chk_hourly.setChecked(self.config.get("hourly_peek", True))
        form_profile.addRow("", self.chk_hourly)

        self.chk_idle = QCheckBox("☕ PC 휴식(유휴 3분) 감지 힐링 알림 (작업 안 할 때 등장)", group_profile)
        self.chk_idle.setChecked(self.config.get("idle_peek", True))
        form_profile.addRow("", self.chk_idle)

        self.combo_scale = QComboBox(group_profile)
        self.combo_scale.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 11px;
                color: #1E293B;
            }
        """)
        scale_presets = [
            ("75% (아담한 미니 화분)", 75),
            ("85% (약간 작게)", 85),
            ("100% (보통 크기 - 기본값)", 100),
            ("115% (약간 크게)", 115),
            ("130% (크게 보기)", 130),
            ("145% (시원한 대형 화분)", 145)
        ]
        curr_s = self.config.get("plant_scale", 100)
        for label, val in scale_presets:
            self.combo_scale.addItem(label, val)
        idx = self.combo_scale.findData(curr_s)
        if idx >= 0:
            self.combo_scale.setCurrentIndex(idx)
        else:
            self.combo_scale.setCurrentIndex(2)
        form_profile.addRow("🔍 화분 크기 조절:", self.combo_scale)

        self.spin_bubble_time = QSpinBox(group_profile)
        self.spin_bubble_time.setRange(3, 30)
        self.spin_bubble_time.setValue(self.config.get("bubble_duration_sec", 4))
        self.spin_bubble_time.setSuffix(" 초")
        form_profile.addRow("말풍선 노출 시간:", self.spin_bubble_time)

        self.spin_decay = QSpinBox(group_profile)
        self.spin_decay.setRange(5, 180)
        self.spin_decay.setValue(self.config.get("decay_interval_minutes", 30))
        self.spin_decay.setSuffix(" 분")
        form_profile.addRow("자연 감쇠 주기:", self.spin_decay)

        layout_plant.addWidget(group_profile)
        layout_plant.addStretch()
        tabs.addTab(tab_plant, "🌱 화분/위젯 설정")

        # Tab 3: Data Management & Reset
        tab_data = QWidget()
        layout_data = QVBoxLayout(tab_data)
        layout_data.setSpacing(12)

        group_reset = QGroupBox("데이터 초기화 및 관리", tab_data)
        layout_btn_group = QVBoxLayout(group_reset)
        layout_btn_group.setSpacing(10)

        btn_clear_chat = QPushButton("🧹 대화 기록 전체 삭제", group_reset)
        btn_clear_chat.setStyleSheet("""
            QPushButton {
                background-color: #FEF3C7;
                border: 1px solid #FCD34D;
                border-radius: 6px;
                padding: 8px;
                color: #92400E;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FDE68A; }
        """)
        btn_clear_chat.clicked.connect(self.on_clear_chat)
        layout_btn_group.addWidget(btn_clear_chat)

        btn_reset_plant = QPushButton("🔄 화분 성장 상태 초기화 (1단계 새싹으로)", group_reset)
        btn_reset_plant.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                border: 1px solid #FCA5A5;
                border-radius: 6px;
                padding: 8px;
                color: #991B1B;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FECACA; }
        """)
        btn_reset_plant.clicked.connect(self.on_reset_plant)
        layout_btn_group.addWidget(btn_reset_plant)

        layout_data.addWidget(group_reset)
        layout_data.addStretch()
        tabs.addTab(tab_data, "💾 데이터 관리")

        layout.addWidget(tabs)

        # Bottom Button Box
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("취소", self)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: #475569;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("저장하기 💾", self)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_save.clicked.connect(self.save_settings)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def save_settings(self):
        """Save form values back to ConfigManager."""
        self.config.set("api_endpoint", self.edit_endpoint.text().strip(), auto_save=False)
        self.config.set("api_key", self.edit_apikey.text().strip(), auto_save=False)
        self.config.set("model", self.edit_model.text().strip(), auto_save=False)
        self.config.set("timeout_sec", self.spin_timeout.value(), auto_save=False)
        self.config.set("ssl_verify", not self.chk_ssl.isChecked(), auto_save=False)
        self.config.set("plant_name", self.edit_plant_name.text().strip() or "초록이", auto_save=False)
        self.config.set("user_nickname", self.edit_user_name.text().strip() or "공직자님", auto_save=False)
        self.config.set("always_on_top", self.chk_ontop.isChecked(), auto_save=False)
        self.config.set("compact_hover_mode", self.chk_compact.isChecked(), auto_save=False)
        self.config.set("ghost_mode", self.chk_ghost.isChecked(), auto_save=False)
        self.config.set("hourly_peek", self.chk_hourly.isChecked(), auto_save=False)
        self.config.set("idle_peek", self.chk_idle.isChecked(), auto_save=False)
        self.config.set("bubble_duration_sec", self.spin_bubble_time.value(), auto_save=False)
        self.config.set("decay_interval_minutes", self.spin_decay.value(), auto_save=False)
        self.config.set("plant_scale", self.combo_scale.currentData(), auto_save=False)

        self.config.save()
        self.settings_saved.emit()
        self.accept()

    def on_preset_changed(self, index: int):
        preset = self.combo_preset.currentData()
        if preset == "gov":
            self.edit_endpoint.setText("https://dev.ai.go.kr/api/v1/chat/completions")
            self.edit_model.setText("gov-gpt-4o")
        elif preset == "openai":
            self.edit_endpoint.setText("https://api.openai.com/v1/chat/completions")
            self.edit_model.setText("gpt-4o-mini")
        elif preset == "ollama":
            self.edit_endpoint.setText("http://localhost:11434/v1/chat/completions")
            self.edit_model.setText("qwen2.5:latest")
            if not self.edit_apikey.text():
                self.edit_apikey.setText("ollama")
        elif preset == "lmstudio":
            self.edit_endpoint.setText("http://localhost:1234/v1/chat/completions")
            self.edit_model.setText("local-model")
            if not self.edit_apikey.text():
                self.edit_apikey.setText("lmstudio")

    def on_test_api_connection(self):
        endpoint = self.edit_endpoint.text().strip()
        api_key = self.edit_apikey.text().strip()
        model = self.edit_model.text().strip()
        timeout = self.spin_timeout.value()
        ssl_verify = not self.chk_ssl.isChecked()

        if not endpoint:
            self.lbl_test_result.setText("<span style='color: #DC2626;'>❌ 엔드포인트를 입력하세요</span>")
            return

        self.lbl_test_result.setText("<span style='color: #2563EB;'>⏳ 연결 확인 중...</span>")
        QApplication.processEvents()

        try:
            import requests
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "안녕! 1단어로만 '안녕'이라고 답해줘."}],
                "max_tokens": 10
            }
            res = requests.post(endpoint, headers=headers, json=payload, timeout=timeout, verify=ssl_verify)
            if res.status_code == 200:
                self.lbl_test_result.setText("<span style='color: #059669;'><b>✅ 연결 성공! (200 OK)</b></span>")
            else:
                self.lbl_test_result.setText(f"<span style='color: #DC2626;'>❌ 오류 (HTTP {res.status_code})</span>")
        except Exception as e:
            self.lbl_test_result.setText(f"<span style='color: #DC2626;'>❌ 연결 실패 ({str(e)[:25]}...)</span>")

    def on_clear_chat(self):
        ret = QMessageBox.question(
            self, "대화 기록 삭제", "정말로 저장된 모든 대화 기록을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.clear_chat_requested.emit()
            QMessageBox.information(self, "완료", "대화 기록이 성공적으로 삭제되었습니다.")

    def on_reset_plant(self):
        ret = QMessageBox.question(
            self, "화분 초기화", "정말로 화분의 성장 상태와 수치를 1단계 새싹으로 초기화하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.reset_plant_requested.emit()
            QMessageBox.information(self, "완료", "화분이 새싹(1단계)으로 초기화되었습니다.")

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

