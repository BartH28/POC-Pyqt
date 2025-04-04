import os
import tkinter as tk
from tkinter import Canvas, Tk
import pyautogui
from PIL import Image

from datetime import datetime

class ScreenCapture:
    def __init__(self, root):
        self.root = root
        self.canvas = Canvas(root, cursor="cross", bg="gray11")
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        # Configura a janela para tela cheia e sem bordas
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.bind("<Escape>", self.cancel_capture)

        # Variáveis para armazenar coordenadas
        self.start_x = None
        self.start_y = None
        self.rect = None

        # Vincula eventos do mouse
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # controla nome e localização dos arquivos
        os.makedirs("images", exist_ok=True)
        self.current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def on_press(self, event):
        # Registra a posição inicial do clique
        self.start_x = event.x_root
        self.start_y = event.y_root

        # Cria um retângulo de seleção
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_drag(self, event):
        # Atualiza o retângulo conforme o mouse é arrastado
        if self.rect:
            self.canvas.coords(
                self.rect,
                self.start_x, self.start_y,
                event.x_root, event.y_root
            )

    def on_release(self, event):
        # Captura as coordenadas finais e fecha a janela
        end_x = event.x_root
        end_y = event.y_root
        self.root.destroy()

        # Calcula a região selecionada
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)

        # Captura a região e salva a imagem
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot.save(f"images/{self.current_time}.png")

    def cancel_capture(self, event):
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    app = ScreenCapture(root)
    root.mainloop()