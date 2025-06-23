import os
import sys
import keyboard
from PyQt6.QtWidgets import QApplication,QSystemTrayIcon, QMessageBox, QMenu, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt6.QtGui import QPixmap, QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QEvent
from tkinter import Tk
from screencapture import ScreenCapture
from PIL import Image
import pytesseract
import sqlite3
import xml.etree.ElementTree as ET

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_PATH,"database","kanjidic_full.db")


# Caminho da pasta onde está o tesseract.exe
def get_tesseract_path():
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como .exe (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Rodando em modo desenvolvimento
        base_path = BASE_PATH

    return os.path.join(base_path, "tesseract", "tesseract.exe")

pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()


class CustomHotkeyEvent(QEvent):
    def __init__(self, tipo):
        super().__init__(QEvent.Type(QEvent.registerEventType()))
        self.tipo = tipo

class DatabaseWorker(QObject):
    resultado_pronto = pyqtSignal(list)  # lista de dicionários com kanji

    def __init__(self, ocr_string):
        super().__init__()
        self.ocr_string = ocr_string
        

    def extract_kanjis(self, string):
        return ''.join(c for c in string if '\u4e00' <= c <= '\u9fff')

    def run(self):
        result_list = []
        print(self.ocr_string)
        kanjis = self.extract_kanjis(self.ocr_string)
        splited_kanjis = list(kanjis)

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                for k in splited_kanjis:
                    cursor.execute("SELECT * FROM kanjidic WHERE kanji = ?", (k,))
                    res = cursor.fetchone()
                    if res:
                        result_list.append({
                            "kanji": res[0],
                            "onyomi": res[1],
                            "kunyomi": res[2],
                            "significado": res[3],
                            "grade": res[4],
                            "jlpt": res[5]
                        })
        except Exception as e:
            print("Erro no worker:", e)
        
        self.resultado_pronto.emit(result_list)

class MeuApp(QWidget):
    def __init__(self):
        super().__init__()
              
        self.setWindowTitle("Test PyQT")
        self.threads_ativas = []
        
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        overlay_width = screen_width // 3
        overlay_heigh = screen_height 
        
        self.setGeometry((screen_width // 3) * 2 , 0, overlay_width, overlay_heigh)  # Tamanho da janela
        
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |  # Mantém a janela sempre no topo
            Qt.WindowType.FramelessWindowHint   # Remove bordas e barra de título
            #Qt.WindowType.X11BypassWindowManagerHint  # Ignora o gerenciador de janelas (Linux)
        )
        # self.setWindowOpacity(0.3);
        # self.setStyleSheet("QWidget{background: #000000}")
        
        self.config_tray()
        
        # Layout vertical
        layout = QVBoxLayout()

        # Botão
        self.botao = QPushButton("Clique aqui ou a tecla F9", self)
        self.botao.clicked.connect(self.capture_button)
        layout.addWidget(self.botao)

        custom_font = QFont()
        custom_font.setWeight(55)
        QApplication.setFont(custom_font, "QLabel")
        
        # Label de saída

        self.resultado_box = QTextEdit()
        self.resultado_box.setReadOnly(True)  # impede edição
        self.resultado_box.setStyleSheet("font-size: 13px; padding: 6px;")
        layout.addWidget(self.resultado_box)

        # self.label_resultado_ocr = QLabel("Resultado ocr aparecerá aqui", self)
        # layout.addWidget(self.label_resultado_ocr)
        
        self.label_resultado = QLabel("Resultado aparecerá aqui", self)
        self.label_resultado.setMinimumSize(600,600)
        layout.addWidget(self.label_resultado, alignment=Qt.AlignmentFlag.AlignCenter)
        self.config_hotkey()

        # Configurar o layout na janela
        self.setLayout(layout)
        
    def event(self, event):
        if isinstance(event, CustomHotkeyEvent):
            if event.tipo == "capture":
                self.capture_button()
            elif event.tipo == "toggle":
                self.toggle_visibility()
            elif event.tipo == "exit":
                self.quit_app()
            return True
        return super().event(event)


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

    def config_hotkey(self):
        self.tree = ET.parse('usersettings.xml', None)
        self.root = self.tree.getroot()

        keyboard.add_hotkey(self.tree.find('capture').get('key'), lambda: QApplication.postEvent(self, CustomHotkeyEvent("capture")))
        keyboard.add_hotkey(self.tree.find('toggle_visibility').get('key'), lambda: QApplication.postEvent(self, CustomHotkeyEvent("toggle")))
        keyboard.add_hotkey(self.tree.find('exit').get('key'), lambda: QApplication.postEvent(self, CustomHotkeyEvent("exit")))

    def capture_button(self):
        """Inicializa a captura de tela, salva a imagem"""   
        try:
            result = self.start_sc()
            result_ocr = pytesseract.image_to_string(f'./images/{result}.png', lang='jpn+eng')
            
            # Inicializa thread e worker
            thread = QThread()
            self.worker = DatabaseWorker(result_ocr)
            self.worker.moveToThread(thread)

            # Conecta sinal ao método que atualiza a interface
            self.worker.resultado_pronto.connect(self.exibir_resultado)
            self.worker.resultado_pronto.connect(thread.quit)
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(lambda: self.threads_ativas.remove(thread))

            self.threads_ativas.append(thread)

            thread.started.connect(self.worker.run)
            thread.start()

            pixmap = QPixmap(f'./images/{result}.png').scaled(self.label_resultado.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
            self.label_resultado.setPixmap(pixmap)
            #self.label_resultado_ocr.setText(result_ocr)
            
            if not self.isVisible():
                self.show()
                self.raise_()  
                self.activateWindow()
        except Exception as e:
            print(e)

    def exibir_resultado(self, result_dict):
        content = ''
        for row in result_dict:
            content += f"""
            <b>Kanji:</b> {row["kanji"]}<br>
            <b>Onyomi:</b> {row["onyomi"]}<br>
            <b>Kunyomi:</b> {row["kunyomi"]}<br>
            <b>Significado:</b> {row["significado"]}<br>
            <b>JLPT:</b> N{row["jlpt"] if row["jlpt"] else "-"}<br>
            <hr>
            """
        self.resultado_box.setHtml(content)

    def show_window(self):
        """Mostra a janela principal."""
        self.show()

    def quit_app(self):
        """Fecha o aplicativo."""
        QApplication.exit()

    # Override no evento de fechar o aplicativo?
    def closeEvent(self, event):
        event.ignore()  # Ignora o evento de fechar
        self.hide()  # Oculta a janela
    
    # Alterna estado de visibilidade Visivel/Invisivel
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()  # Garante que apareça em frente às outras janelas
            self.activateWindow()

    def start_sc(self):
        root = Tk()
        app = ScreenCapture(root)
        root.mainloop()
        return app.current_time 

    
# Inicializar o app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Erro", "Systray não suportado neste sistema.")
        exit(1)
    
    # Verifica se existe o arquivo xml que armazena as hotkeys do
    if not os.path.exists('usersettings.xml'):
    # Cria arquivo xml
        data = ET.Element('hotkeys')

        element1 = ET.SubElement(data, 'exit')
        element1.set('key', 'f4')
        
        element2 = ET.SubElement(data, 'capture')
        element2.set('key', 'f9')

        element3 = ET.SubElement(data, 'toggle_visibility')
        element3.set('key', 'f10')

        b_xml = ET.tostring(data)
        with open("usersettings.xml", "wb") as f:
            f.write(b_xml)
        
    janela = MeuApp()
    janela.show()

    
    sys.exit(app.exec())
