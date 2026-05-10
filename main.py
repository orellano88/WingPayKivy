from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Line, Mesh
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.lang import Builder
from datetime import datetime
import threading
import os
import requests
import json
import math

# Intento de importar plyer para TTS (Text-to-Speech) nativo en Android
try:
    from plyer import tts, vibrator
except ImportError:
    tts = None
    vibrator = None

# --- MOTOR PRINCIPAL: WING PAY SENTINEL v39.0 (STARK GLASS EDITION) ---
class MessageBubble(BoxLayout):
    text = StringProperty("")
    source = StringProperty("")
    is_user = BooleanProperty(True)
    is_payment = BooleanProperty(False)
    bank = StringProperty("YAPE")
    time = StringProperty("")
    bg_color = ListProperty([1, 1, 1, 0.15])
    border_color = ListProperty([1, 1, 1, 0.3])
    halign = StringProperty("right")
    has_image = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.spacing = 5
        self.bind(minimum_height=self.setter('height'))

class WingPaySentinel(BoxLayout):
    status_ntfy = StringProperty("🔴") 
    status_pc = StringProperty("⚪")
    pulse_color = ListProperty([0.04, 0.6, 0.35, 0.5])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.start_sync_listener()
        Clock.schedule_interval(self._update_pulse, 0.05)

    def _update_pulse(self, dt):
        alpha = (math.sin(Clock.get_time() * 3) + 1) / 4 + 0.2
        self.pulse_color[3] = alpha

    def start_sync_listener(self):
        threading.Thread(target=self.ntfy_listener, daemon=True).start()

    def ntfy_listener(self):
        topic = "wingpay_stark_8502345704"
        url = f"https://ntfy.sh/{topic}/json"
        while True:
            try:
                with requests.get(url, stream=True, timeout=None) as r:
                    self.status_ntfy = "🟢"
                    for line in r.iter_lines():
                        if line:
                            self.status_pc = "🔵"
                            data = json.loads(line)
                            if "message" in data:
                                try:
                                    msg_data = json.loads(data["message"])
                                    self.inject_payment_notification(
                                        msg_data.get("bank", "YAPE"), 
                                        f"S/ {msg_data.get('amt', '0.00')} de {msg_data.get('name', 'Cliente')}"
                                    )
                                except: pass
                            Clock.schedule_once(lambda dt: setattr(self, 'status_pc', "⚪"), 2)
            except:
                self.status_ntfy = "🔴"
                import time
                time.sleep(15)

    @mainthread
    def inject_payment_notification(self, bank, details):
        msg = f"¡Transferencia exitosa!\n{details}"
        self.add_message(msg, is_user=False, is_payment=True, bank=bank)
        self.play_audio_alert(bank, details)

    def play_audio_alert(self, bank, details):
        monto = "un pago"
        if "S/" in details:
            parts = details.split("S/")
            if len(parts) > 1: monto = f"S/ {parts[1].split()[0]}"
        nombre = details.replace(f"por {monto}", "").replace(monto, "").replace("de", "").replace("¡Transferencia exitosa!", "").strip()
        speech_text = f"Atención. Pago recibido en {bank}. {nombre} envió {monto}."
        if tts: threading.Thread(target=lambda: tts.speak(speech_text)).start()

    def trigger_panic(self):
        if vibrator: vibrator.vibrate(1)
        self.add_message("🚨 ALARMA DE PÁNICO ACTIVADA 🚨", is_user=True)

    def send_action(self, text_input):
        msg = text_input.text.strip()
        if msg:
            text_input.text = ""
            self.add_message(msg, is_user=True)
            if msg.lower() == "test yape":
                self.inject_payment_notification("YAPE", "S/ 50.00 de Juan Perez")

    @mainthread
    def add_message(self, text, is_user=True, is_payment=False, bank="YAPE", source=""):
        if is_payment:
            bg = [1, 1, 1, 0.2]
            border = [0.1, 0.8, 0.4, 0.6] if bank == "YAPE" else [1, 0.6, 0.1, 0.6]
        else:
            bg = [1, 1, 1, 0.15] if is_user else [1, 1, 1, 0.25]
            border = [1, 1, 1, 0.3]
        
        new_entry = {
            "text": text,
            "source": source,
            "has_image": True if source else False,
            "is_user": is_user,
            "is_payment": is_payment,
            "bank": bank,
            "time": datetime.now().strftime("%H:%M"),
            "bg_color": bg,
            "border_color": border,
            "halign": "right" if is_user else ("center" if is_payment else "left")
        }
        self.ids.rv.data.append(new_entry)
        self.ids.rv.scroll_y = 0

class WingPayApp(App):
    def build(self):
        return Builder.load_string('''
<MessageBubble>:
    padding: [10, 5]
    AnchorLayout:
        anchor_x: root.halign
        BoxLayout:
            orientation: 'vertical'
            size_hint: None, None
            width: min(Window.width * 0.75, self.minimum_width + 30) if not root.has_image else '260dp'
            height: self.minimum_height
            padding: [15, 12]
            canvas.before:
                Color:
                    rgba: root.bg_color
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [18, 18, 2, 18] if root.is_user else [18, 18, 18, 2]
                Color:
                    rgba: root.border_color
                Line:
                    width: 1.2
                    rounded_rectangle: (self.x, self.y, self.width, self.height, 18, 18, 2, 18) if root.is_user else (self.x, self.y, self.width, self.height, 18, 18, 18, 2)

            AsyncImage:
                source: root.source
                size_hint_y: None
                height: '220dp' if root.has_image else 0
                opacity: 1 if root.has_image else 0
                allow_stretch: True

            Label:
                text: root.text
                color: 1, 1, 1, 1
                font_size: '16sp'
                size_hint: 1, None
                height: self.texture_size[1]
                text_size: self.width, None
                halign: 'left'
                bold: root.is_payment

            Label:
                text: root.time
                color: 1, 1, 1, 0.6
                font_size: '11sp'
                size_hint_y: None
                height: '18dp'
                halign: 'right'
                text_size: self.size

WingPaySentinel:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Mesh:
                mode: 'triangle_fan'
                vertices: [self.x, self.y, 0, 0, 0.05, 0.12, 0.15, 1, self.right, self.y, 0, 0, 0.12, 0.22, 0.26, 1, self.right, self.top, 0, 0, 0.15, 0.25, 0.28, 1, self.x, self.top, 0, 0, 0.05, 0.12, 0.15, 1]
                indices: [0, 1, 2, 3]

        BoxLayout:
            size_hint_y: None
            height: '90dp'
            padding: '15dp'
            spacing: '10dp'
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 0.1
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            BoxLayout:
                orientation: 'vertical'
                Label:
                    text: "WING PAY KIVY STARK"
                    bold: True
                    font_size: '20sp'
                    halign: 'left'
                    text_size: self.size
                Label:
                    text: f"RED: {root.status_ntfy}  SYNC: {root.status_pc}"
                    font_size: '13sp'
                    color: 0.8, 0.9, 1, 1
                    halign: 'left'
                    text_size: self.size

            Widget:
                size_hint: None, None
                size: '40dp', '40dp'
                canvas:
                    Color:
                        rgba: root.pulse_color
                    Ellipse:
                        pos: self.x, self.y
                        size: self.size
                    Color:
                        rgba: 1, 1, 1, 0.8
                    Line:
                        width: 1.5
                        circle: (self.center_x, self.center_y, 15)

            Button:
                text: "🚨"
                size_hint_x: None
                width: '60dp'
                background_color: 0.8, 0.1, 0.1, 0.6
                on_release: root.trigger_panic()

        RecycleView:
            id: rv
            viewclass: 'MessageBubble'
            RecycleBoxLayout:
                default_size: None, None
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                spacing: '15dp'
                padding: '15dp'

        BoxLayout:
            size_hint_y: None
            height: '80dp'
            padding: '10dp'
            spacing: '12dp'
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 0.08
                Rectangle:
                    pos: self.pos
                    size: self.size

            TextInput:
                id: ti
                hint_text: "Mensaje Stark..."
                multiline: False
                background_color: 1, 1, 1, 0.1
                foreground_color: 1, 1, 1, 1
                cursor_color: 0, 0.8, 1, 1
                on_text_validate: root.send_action(ti)
            
            Button:
                text: "➤"
                size_hint_x: None
                width: '60dp'
                background_color: 0, 0.5, 0.8, 0.6
                on_release: root.send_action(ti)
''')

if __name__ == '__main__':
    WingPayApp().run()
