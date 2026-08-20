"""
Main Entry Point for AI Companion Plant Widget
(범정부 AI API 기반 데스크톱 플로팅 AI 반려화분 위젯)
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from ai_plant.config import ConfigManager, get_resource_path
from ai_plant.database import DatabaseManager
from ai_plant.plant_engine import PlantEngine
from ai_plant.ui.floating_widget import FloatingPlantWindow
from ai_plant.ui.welcome_dialog import WelcomeSetupDialog

def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AI Companion Plant")
    app.setOrganizationName("GovAI")
    app.setQuitOnLastWindowClosed(False)  # Keep desktop companion plant alive when dialogs close
    app.setStyleSheet("""
        QMenu {
            background-color: #FFFFFF;
            color: #1E293B;
            border: 1px solid #CBD5E1;
            font-family: 'Malgun Gothic', 'Segoe UI';
        }
        QMenu::item {
            color: #1E293B;
            background-color: transparent;
        }
        QMenu::item:selected {
            background-color: #ECFDF5;
            color: #065F46;
        }
        QToolTip {
            background-color: #1E293B;
            color: #FFFFFF;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
        }
    """)

    # Single-Instance Enforcement to prevent duplicate overlapping windows
    server_name = "AICompanionPlant_SingleInstance_GovAI"
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if socket.waitForConnected(400):
        # Another instance is already running; request activation and exit
        socket.write(b"ACTIVATE")
        socket.flush()
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        sys.exit(0)

    # Clean up stale socket file and listen
    QLocalServer.removeServer(server_name)
    single_instance_server = QLocalServer()
    single_instance_server.listen(server_name)

    # Set App Icon
    icon_path = get_resource_path(os.path.join("assets", "stage_4.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Initialize Core Managers
    config_mgr = ConfigManager()
    db_mgr = DatabaseManager()
    config_mgr.set_db(db_mgr)
    plant_engine = PlantEngine(db_mgr, config_mgr)

    # Launch Floating Widget
    window = FloatingPlantWindow(plant_engine, db_mgr, config_mgr)

    def handle_activation():
        client = single_instance_server.nextPendingConnection()
        if client:
            client.waitForReadyRead(400)
            data = client.readAll().data().decode("utf-8", errors="ignore")
            if "ACTIVATE" in data:
                window.show()
                window.raise_()
                window.activateWindow()
            client.disconnectFromServer()

    single_instance_server.newConnection.connect(handle_activation)

    # First launch: Onboarding setup dialog for Name, Species & User Nickname
    if not config_mgr.get("initial_setup_done", False):
        welcome_dlg = WelcomeSetupDialog(config_mgr, plant_engine)
        welcome_dlg.exec()
        window.apply_settings_changes()
        plant_engine.check_achievements()

    app.aboutToQuit.connect(window.cleanup_threads)
    window.show()

    exit_code = app.exec()
    single_instance_server.close()
    QLocalServer.removeServer(server_name)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
