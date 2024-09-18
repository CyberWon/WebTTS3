# coding:utf-8
import os
import sys
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(sys.path[0]))
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.view.main_window import MainWindow
import PySide6.QtAsyncio as QtAsyncio
from tts.api import HTTPAPI
import asyncio
from qasync import QEventLoop, QApplication

# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

# create application
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
event_loop = QEventLoop(app)
asyncio.set_event_loop(event_loop)

app_close_event = asyncio.Event()
app.aboutToQuit.connect(app_close_event.set)

# fixes issue: https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/848
if sys.platform == 'win32' and sys.getwindowsversion().build >= 22000:
    app.setStyle("fusion")

# internationalization
locale = cfg.get(cfg.language).value
translator = FluentTranslator(locale)
galleryTranslator = QTranslator()
galleryTranslator.load(locale, "gallery", ".", ":/gallery/i18n")

app.installTranslator(translator)
app.installTranslator(galleryTranslator)

# create main window
w = MainWindow()
w.show()

with event_loop:
    event_loop.run_until_complete(app_close_event.wait())
