import subprocess
import sys
import keyboard
from PyQt6.QtWidgets import QApplication,QSystemTrayIcon, QMessageBox, QMenu, QWidget, QVBoxLayout, QPushButton, QLabel, QStyleFactory
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QIcon, QAction
from PyQt6.QtCore import Qt 

class MeuApp(QWidget):
    def __init__(self):
        super().__init__()
              
        self.setWindowTitle("Test PyQT")
        
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        overlay_width = screen_width // 3
        overlay_heigh = screen_height 
        
        self.setGeometry(0, 0, overlay_width, overlay_heigh)  # Tamanho da janela
        
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint #|  # Mantém a janela sempre no topo
            #Qt.WindowType.FramelessWindowHint    # Remove bordas e barra de título
           # Qt.WindowType.X11BypassWindowManagerHint  # Ignora o gerenciador de janelas (Linux)
        )
        # self.setWindowOpacity(0.3);
        # self.setStyleSheet("QWidget{background: #000000}")
        
        self.config_tray()
        
        # Layout vertical
        layout = QVBoxLayout()

        # Botão
        self.botao = QPushButton("Clique aqui ou a tecla F9", self)
        self.botao.clicked.connect(self.acao_botao)
        layout.addWidget(self.botao)
        
        # Label de saída
        self.label_resultado = QLabel("Resultado aparecerá aqui", self)
        self.label_resultado.setMinimumSize(600,600)
        
        #self.resize(pixmap.width(),pixmap.height)
        
        layout.addWidget(self.label_resultado, alignment=Qt.AlignmentFlag.AlignCenter)

        keyboard.add_hotkey("f9", self.acao_botao)
        
        # Configurar o layout na janela
        self.setLayout(layout)
        
    def config_tray(self):
        #Tray Config
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png")) 
        self.tray_menu = QMenu()
        
        self.show_action = QAction("Mostrar", self)
        self.show_action.triggered.connect(self.show_window)
        self.tray_menu.addAction(self.show_action)
    
        
        self.quit_action = QAction("Sair", self)
        self.quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(self.quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)

        self.tray_icon.show()

    def acao_botao(self):
        subprocess.run([sys.executable, "test.py"])
        pixmap = QPixmap("./captura_area.png").scaled(self.label_resultado.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.label_resultado.setPixmap(pixmap)
        self.show()
        
    def show_window(self):
        """Mostra a janela principal."""
        self.show()

    def quit_app(self):
        """Fecha o aplicativo."""
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()  # Ignora o evento de fechar
        self.hide()  # Oculta a janela
        
        
# Inicializar o app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Erro", "Systray não suportado neste sistema.")
        exit(1)
        
    janela = MeuApp()
    janela.show()
    sys.exit(app.exec())
