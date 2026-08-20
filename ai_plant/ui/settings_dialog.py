"""
Settings Dialog Widget
Allows users to configure CLOVA Studio GOV / OpenAI API endpoints, API Key, intranet SSL bypass,
streaming options, plant names, proactive speech triggers, and decay rates.
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
        self.resize(500, 480)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
                color: #1E293B;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #334155;
                background: transparent;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 14px;
                background-color: #FFFFFF;
                color: #0F766E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #0F766E;
            }
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                background-color: #F8FAFC;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #E2E8F0;
                color: #475569;
                padding: 7px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #0F766E;
                border-bottom: 2px solid #10B981;
            }
            QTabBar::tab:hover {
                color: #0F766E;
                background-color: #F1F5F9;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1.5px solid #10B981;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #1E293B;
                selection-background-color: #ECFDF5;
                selection-color: #065F46;
                border: 1px solid #CBD5E1;
            }
            QCheckBox {
                color: #334155;
                font-size: 11px;
                background: transparent;
                spacing: 6px;
            }
            QCheckBox:hover {
                color: #0F766E;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header Row (Title + Close Button)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 4)

        title_lbl = QLabel("⚙️ <b>환경 설정</b>", self)
        title_lbl.setStyleSheet("color: #334155; font-size: 14px;")

        self.btn_header_close = QPushButton("닫기 ✕", self)
        self.btn_header_close.setAutoDefault(False)
        self.btn_header_close.setDefault(False)
        self.btn_header_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_header_close.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                color: #64748B;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                border-color: #FCA5A5;
                color: #DC2626;
            }
        """)
        self.btn_header_close.clicked.connect(self.close)

        header_row.addWidget(title_lbl, 1)
        header_row.addWidget(self.btn_header_close, 0)
        layout.addLayout(header_row)

        # Tabs
        tabs = QTabWidget(self)

        # Tab 1: AI API Settings
        tab_api = QWidget()
        layout_api = QVBoxLayout(tab_api)
        layout_api.setSpacing(10)

        group_api = QGroupBox("CLOVA Studio GOV / 공공 AI / LLM 연동 설정", tab_api)
        form_api = QFormLayout(group_api)
        form_api.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_api.setSpacing(8)

        # Provider Presets
        self.combo_preset = QComboBox(group_api)
        self.combo_preset.addItem("CLOVA Studio GOV (api.clovastudio.go.kr)", "clova_gov")
        self.combo_preset.addItem("범정부 AI (dev.ai.go.kr)", "gov")
        self.combo_preset.addItem("OpenAI (api.openai.com)", "openai")
        self.combo_preset.addItem("로컬 Ollama (localhost:11434)", "ollama")
        self.combo_preset.addItem("로컬 LM Studio (localhost:1234)", "lmstudio")
        self.combo_preset.addItem("직접 입력 (Custom URL)", "custom")
        self.combo_preset.currentIndexChanged.connect(self.on_preset_changed)
        form_api.addRow("API 프리셋:", self.combo_preset)

        self.edit_endpoint = QLineEdit(group_api)
        self.edit_endpoint.setText(self.config.get("api_endpoint", "https://api.clovastudio.go.kr/api/v1/chat/completions"))
        self.edit_endpoint.setPlaceholderText("https://api.clovastudio.go.kr/api/v1/chat/completions")
        form_api.addRow("API 엔드포인트:", self.edit_endpoint)

        self.edit_apikey = QLineEdit(group_api)
        self.edit_apikey.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_apikey.setText(self.config.get("api_key", ""))
        self.edit_apikey.setPlaceholderText("발급받은 AI API Key 입력 (로컬은 생략 가능)")
        form_api.addRow("API Key:", self.edit_apikey)

        self.edit_model = QLineEdit(group_api)
        self.edit_model.setText(self.config.get("model", "HCX-GOV-THINK-V1-32B"))
        form_api.addRow("모델명 (Model):", self.edit_model)

        self.spin_timeout = QSpinBox(group_api)
        self.spin_timeout.setRange(2, 60)
        self.spin_timeout.setValue(self.config.get("timeout_sec", 10))
        self.spin_timeout.setSuffix(" 초")
        form_api.addRow("요청 타임아웃:", self.spin_timeout)

        self.chk_stream = QCheckBox("실시간 토큰 스트리밍 (stream: true) 활성화", group_api)
        self.chk_stream.setChecked(self.config.get("stream_enabled", True))
        form_api.addRow("", self.chk_stream)

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

        self.chk_proactive = QCheckBox("🌿 화분의 자발적 말걸기 (상태이상/1.5시간 넛지/점심·퇴근 인사) 활성화", group_profile)
        self.chk_proactive.setChecked(self.config.get("proactive_speech", True))
        form_profile.addRow("", self.chk_proactive)

        self.chk_ontop = QCheckBox("항상 화면 최상위에 고정 (Always On Top)", group_profile)
        self.chk_ontop.setChecked(self.config.get("always_on_top", True))
        form_profile.addRow("", self.chk_ontop)

        self.chk_compact = QCheckBox("✨ 클릭 시 메뉴 표시 모드 (화분 클릭 시 메뉴 토글)", group_profile)
        self.chk_compact.setChecked(self.config.get("compact_hover_mode", True))
        form_profile.addRow("", self.chk_compact)

        self.chk_ghost = QCheckBox("👻 고스트 반투명 모드 (평소 반투명, 마우스 올리면 선명화)", group_profile)
        self.chk_ghost.setChecked(self.config.get("ghost_mode", False))
        form_profile.addRow("", self.chk_ghost)

        self.combo_scale = QComboBox(group_profile)
        self.combo_scale.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
        """)
        for sc in [70, 80, 90, 100, 110, 120, 130, 140, 150]:
            self.combo_scale.addItem(f"{sc}%", sc)
        curr_scale = self.config.get("plant_scale", 100)
        idx = self.combo_scale.findData(curr_scale)
        if idx >= 0:
            self.combo_scale.setCurrentIndex(idx)
        form_profile.addRow("화분 크기 배율:", self.combo_scale)

        self.spin_bubble_time = QSpinBox(group_profile)
        self.spin_bubble_time.setRange(2, 15)
        self.spin_bubble_time.setValue(self.config.get("bubble_duration_sec", 5))
        self.spin_bubble_time.setSuffix(" 초")
        form_profile.addRow("말풍선 지속 시간:", self.spin_bubble_time)

        self.spin_decay = QSpinBox(group_profile)
        self.spin_decay.setRange(5, 180)
        self.spin_decay.setValue(self.config.get("decay_interval_minutes", 30))
        self.spin_decay.setSuffix(" 분")
        form_profile.addRow("상태 감소 주기:", self.spin_decay)

        layout_plant.addWidget(group_profile)
        layout_plant.addStretch()
        tabs.addTab(tab_plant, "🌱 화분 & 인터랙션")

        # Tab 3: Data Management
        tab_data = QWidget()
        layout_data = QVBoxLayout(tab_data)
        layout_data.setSpacing(12)

        group_danger = QGroupBox("데이터 초기화 및 관리", tab_data)
        layout_danger = QVBoxLayout(group_danger)
        layout_danger.setSpacing(10)

        lbl_warn = QLabel("⚠️ 데이터 초기화 작업은 되돌릴 수 없으므로 신중히 선택해주세요.")
        lbl_warn.setStyleSheet("color: #DC2626; font-size: 11px;")
        layout_danger.addWidget(lbl_warn)

        btn_clear_chat = QPushButton("🗑️ 대화 기록만 초기화", group_danger)
        btn_clear_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_chat.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
                border-radius: 6px;
                padding: 8px 12px;
                color: #B91C1C;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FEE2E2; }
        """)
        btn_clear_chat.clicked.connect(self.on_clear_chat)
        layout_danger.addWidget(btn_clear_chat)

        btn_reset_plant = QPushButton("🔄 화분 성장 상태 초기화 (1단계 새싹으로 리셋)", group_danger)
        btn_reset_plant.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_plant.setStyleSheet("""
            QPushButton {
                background-color: #FFF1F2;
                border: 1px solid #FFE4E6;
                border-radius: 6px;
                padding: 8px 12px;
                color: #BE123C;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FFE4E6; }
        """)
        btn_reset_plant.clicked.connect(self.on_reset_plant)
        layout_danger.addWidget(btn_reset_plant)

        layout_data.addWidget(group_danger)
        layout_data.addStretch()
        tabs.addTab(tab_data, "💾 데이터 관리")

        layout.addWidget(tabs)

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("취소", self)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 16px;
                color: #475569;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        self.btn_cancel.clicked.connect(self.close)

        self.btn_save = QPushButton("💾 설정 저장", self)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_save.clicked.connect(self.save_settings)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

    def save_settings(self):
        """Save form values back to ConfigManager."""
        self.config.set("api_endpoint", self.edit_endpoint.text().strip(), auto_save=False)
        self.config.set("api_key", self.edit_apikey.text().strip(), auto_save=False)
        self.config.set("model", self.edit_model.text().strip(), auto_save=False)
        self.config.set("timeout_sec", self.spin_timeout.value(), auto_save=False)
        self.config.set("stream_enabled", self.chk_stream.isChecked(), auto_save=False)
        self.config.set("ssl_verify", not self.chk_ssl.isChecked(), auto_save=False)
        self.config.set("plant_name", self.edit_plant_name.text().strip() or "초록이", auto_save=False)
        self.config.set("user_nickname", self.edit_user_name.text().strip() or "공직자님", auto_save=False)
        self.config.set("proactive_speech", self.chk_proactive.isChecked(), auto_save=False)
        self.config.set("always_on_top", self.chk_ontop.isChecked(), auto_save=False)
        self.config.set("compact_hover_mode", self.chk_compact.isChecked(), auto_save=False)
        self.config.set("ghost_mode", self.chk_ghost.isChecked(), auto_save=False)
        self.config.set("bubble_duration_sec", self.spin_bubble_time.value(), auto_save=False)
        self.config.set("decay_interval_minutes", self.spin_decay.value(), auto_save=False)
        self.config.set("plant_scale", self.combo_scale.currentData(), auto_save=False)

        self.config.save()
        self.settings_saved.emit()
        self.close()

    def on_preset_changed(self, index: int):
        preset = self.combo_preset.currentData()
        if preset == "clova_gov":
            self.edit_endpoint.setText("https://api.clovastudio.go.kr/api/v1/chat/completions")
            self.edit_model.setText("HCX-GOV-THINK-V1-32B")
            self.chk_stream.setChecked(True)
        elif preset == "gov":
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

    def accept(self):
        """Save settings and close on accept."""
        self.save_settings()

    def reject(self):
        self.close()

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
