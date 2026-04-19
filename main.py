from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from datetime import datetime
import threading
import os

# Intento de importar plyer para TTS (Text-to-Speech) nativo en Android
try:
    from plyer import tts, vibrator
except ImportError:
    tts = None
    vibrator = None

# --- PROTOCOLO JARVIS-QWEN v36.0: SENTINEL EDITION (MACRODROID CLONE) ---
# 1. Cabecera con Botón de Pánico.
# 2. Captura de Notificaciones (Yape/BCP).
# 3. Burbujas de Pago Especiales (Marcos y colores distintivos).
# 4. Reproducción Automática de Audio (TTS).

class Bubble(BoxLayout):
    def __init__(self, text, is_user=True, is_payment=False, bank="YAPE", path=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = [15, 10]
        self.spacing = 5
        
        # Lógica de Colores y Marcos
        if is_payment:
            # Marco especial para pagos (Yape: Morado, BCP: Naranja)
            self.bg_color = (0.9, 0.8, 1, 1) if bank == "YAPE" else (1, 0.85, 0.7, 1)
            border_color = (0.5, 0.1, 0.7, 1) if bank == "YAPE" else (1, 0.5, 0, 1)
            self.align = 'center' # Los pagos van al centro como notificaciones globales
        else:
            self.bg_color = (0.88, 0.99, 0.78, 1) if is_user else (1, 1, 1, 1)
            border_color = self.bg_color
            self.align = 'right' if is_user else 'left'
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15, 15, 15, 15])
            if is_payment:
                Color(*border_color)
                self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 15), width=2)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Si es un pago, agregar título del banco
        if is_payment:
            bank_lbl = Label(text=f"💰 PAGO RECIBIDO: {bank}", color=border_color, bold=True, size_hint=(None, None), font_size='12sp')
            bank_lbl.bind(texture_size=bank_lbl.setter('size'))
            self.add_widget(bank_lbl)

        # Contenido Multimedia
        if path and os.path.exists(path):
            img = Image(source=path, size_hint=(None, None), size=(200, 200), allow_stretch=True)
            self.add_widget(img)
        
        # Texto del Mensaje
        lbl = Label(text=text, color=(0,0,0,1), size_hint=(None, None), font_size='15sp', bold=is_payment)
        lbl.bind(texture_size=lbl.setter('size'))
        self.add_widget(lbl)
        
        # Hora Actual
        time_str = datetime.now().strftime("%H:%M")
        time_lbl = Label(text=time_str, color=(0.5, 0.5, 0.5, 1), size_hint=(None, None), font_size='10sp', halign='right')
        time_lbl.bind(texture_size=time_lbl.setter('size'))
        self.add_widget(time_lbl)

        self.bind(minimum_height=self.setter('height'))
        self.width = 320 if is_payment else 280

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        if hasattr(self, 'border'):
            self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, 15)

class WingPaySentinel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        Window.clearcolor = (0.94, 0.95, 0.96, 1)
        self.start_sync_listener()

    def start_sync_listener(self):
        # Escucha Global Stark (ntfy.sh)
        threading.Thread(target=self.ntfy_listener, daemon=True).start()

    def ntfy_listener(self):
        topic = "wingpay_stark_8502345704"
        url = f"https://ntfy.sh/{topic}/json"
        while True:
            try:
                import requests
                import json
                with requests.get(url, stream=True, timeout=60) as r:
                    for line in r.iter_lines():
                        if line:
                            data = json.loads(line)
                            if "message" in data:
                                try:
                                    msg_data = json.loads(data["message"])
                                    Clock.schedule_once(lambda dt: self.inject_payment_notification(
                                        msg_data.get("bank", "YAPE"), 
                                        f"S/ {msg_data.get('amt', '0.00')} de {msg_data.get('name', 'Cliente')}"
                                    ), 0)
                                except: pass
            except:
                import time
                time.sleep(10)

    # --- 1. CABECERA TÁCTICA CON BOTÓN DE PÁNICO ---
        self.header = BoxLayout(size_hint_y=None, height=60, background_color=(0.03, 0.35, 0.38, 1))
        with self.header.canvas.before:
            Color(0.03, 0.35, 0.38, 1) # Verde oscuro institucional
            RoundedRectangle(pos=self.header.pos, size=self.header.size)
        self.header.bind(pos=self.update_header, size=self.update_header)
        
        title = Label(text="WING PAY SENTINEL", bold=True, font_size='18sp', size_hint_x=0.8)
        self.btn_panic = Button(text="🚨", background_color=(1, 0, 0, 1), size_hint_x=0.2, bold=True)
        self.btn_panic.bind(on_press=self.trigger_panic)
        
        self.header.add_widget(title)
        self.header.add_widget(self.btn_panic)
        self.add_widget(self.header)

        # --- 2. ZONA DE CHAT Y SCROLL ---
        self.scroll = ScrollView(do_scroll_x=False, padding=[10,10])
        self.chat_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=[10, 20])
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        
        self.scroll.add_widget(self.chat_list)
        self.add_widget(self.scroll)

        # --- 3. BARRA DE ENTRADA ---
        self.input_area = BoxLayout(size_hint_y=None, height=60, spacing=10, padding=5)
        self.text_input = TextInput(hint_text='Escribe al Espejo...', multiline=False, size_hint_x=0.8)
        self.send_btn = Button(text='>', size_hint_x=0.2, background_color=(0.03, 0.75, 0.38, 1), bold=True)
        self.send_btn.bind(on_press=self.send_action)

        self.input_area.add_widget(self.text_input)
        self.input_area.add_widget(self.send_btn)
        self.add_widget(self.input_area)

        # Iniciar Simulador de Intercepción de Notificaciones (MacroDroid Style)
        self.start_notification_listener()

    def update_header(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.03, 0.35, 0.38, 1)
            RoundedRectangle(pos=instance.pos, size=instance.size)

    def trigger_panic(self, instance):
        # Lógica del Botón de Pánico
        if vibrator: vibrator.vibrate(1)
        self.add_message("🚨 ALARMA DE PÁNICO ACTIVADA 🚨", is_user=True)
        # Aquí se ejecutaría el bloqueo del sistema o envío de SMS de emergencia

    def send_action(self, instance):
        msg = self.text_input.text.strip()
        if msg:
            self.text_input.text = "" # Limpieza Inmediata
            self.add_message(msg, is_user=True)
            # Simular test de pago Yape escribiendo "test yape"
            if msg.lower() == "test yape":
                Clock.schedule_once(lambda dt: self.inject_payment_notification("YAPE", "S/ 50.00 de Juan Perez"), 1)
            elif msg.lower() == "test bcp":
                Clock.schedule_once(lambda dt: self.inject_payment_notification("BCP", "S/ 120.00 de Maria Gomez"), 1)

    def add_message(self, text, is_user=True, is_payment=False, bank="YAPE", path=None):
        if is_payment:
            anchor = 'center'
        else:
            anchor = 'right' if is_user else 'left'
            
        container = AnchorLayout(anchor_x=anchor, size_hint_y=None)
        bubble = Bubble(text=text, is_user=is_user, is_payment=is_payment, bank=bank, path=path)
        
        container.add_widget(bubble)
        container.height = bubble.height
        
        self.chat_list.add_widget(container)
        bubble.bind(height=lambda *a: setattr(container, 'height', bubble.height))
        
        Clock.schedule_once(self.update_scroll, 0.1)

    def update_scroll(self, dt):
        self.scroll.scroll_y = 0

    # --- MOTOR DE INTERCEPCIÓN Y AUDIO (ESTILO MACRODROID) ---
    def start_notification_listener(self):
        # En Android Real, aquí se usa PyJnius para conectar con NotificationListenerService
        # Para el prototipo, dejamos el hilo listo escuchando eventos del sistema
        threading.Thread(target=self._background_listener, daemon=True).start()

    def _background_listener(self):
        # Simula estar escuchando...
        pass

    def inject_payment_notification(self, bank, details):
        # 1. Mostrar la Burbuja Especial
        msg = f"¡Transferencia exitosa!\n{details}"
        self.add_message(msg, is_user=False, is_payment=True, bank=bank)
        
        # 2. Reproducir Audio Automáticamente (TTS)
        self.play_audio_alert(bank, details)

    def play_audio_alert(self, bank, details):
        monto = "un pago"
        if "S/" in details:
            parts = details.split("S/")
            if len(parts) > 1:
                monto = f"S/ {parts[1].split()[0]}"
        
        nombre = details.replace(f"por {monto}", "").replace(monto, "").replace("de", "").replace("¡Transferencia exitosa!", "").strip()
        
        speech_text = f"Atención. Pago recibido en {bank}. {nombre} envió {monto}."
        if tts:
            try:
                tts.speak(speech_text)
            except Exception as e:
                print(f"Error TTS: {e}")
        else:
            # Si plyer no está instalado en la PC, imprimimos en consola
            print(f"[AUDIO SIMULADO]: 🔊 '{speech_text}'")

class WingPayApp(App):
    def build(self):
        return WingPaySentinel()

if __name__ == '__main__':
    WingPayApp().run()
