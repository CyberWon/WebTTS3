# coding:utf-8
import json
import os

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPainterPath, QLinearGradient
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from loguru import logger

from qfluentwidgets import ScrollArea, isDarkTheme, FluentIcon, PrimaryToolButton, TransparentToggleToolButton, \
    PushButton
from ..common.config import cfg, BUY_NOVEL_DUB, BUY_AI_DUB
from ..common.icon import Icon, FluentIconBase
from ..components.link_card import LinkCardView
from ..components.sample_card import SampleCardView
from ..common.style_sheet import StyleSheet
from qfluentwidgets import FluentIcon as FIF
from WebTTS3.tts.api import HTTPAPI


class BannerWidget(QWidget):
    """ Banner widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(336)

        self.vBoxLayout = QVBoxLayout(self)
        self.galleryLabel = QLabel('WebTTS3', self)
        self.banner = QPixmap(':/gallery/images/header1.png')
        self.linkCardView = LinkCardView(self)

        self.galleryLabel.setObjectName('galleryLabel')

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 20, 0, 0)
        self.vBoxLayout.addWidget(self.galleryLabel)
        self.vBoxLayout.addWidget(self.linkCardView, 1, Qt.AlignBottom)
        self.vBoxLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.linkCardView.addCard(
            ':/gallery/ico/ai_dub.ico',
            self.tr('AI配音'),
            self.tr('专业的AI配音工具，支持多种语音引擎和本项目。'),
            BUY_AI_DUB
        )

        self.linkCardView.addCard(
            ':/gallery/ico/novel_dub.ico',
            self.tr('AI有声读物'),
            self.tr(
                '为有声读物领域用户打造的AI创作工具，支持LLM和多种配音选择。'),
            BUY_NOVEL_DUB
        )

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        w, h = self.width(), self.height()
        path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
        path.addRect(QRectF(0, h - 50, 50, 50))
        path.addRect(QRectF(w - 50, 0, 50, 50))
        path.addRect(QRectF(w - 50, h - 50, 50, 50))
        path = path.simplified()

        # init linear gradient effect
        gradient = QLinearGradient(0, 0, 0, h)

        # draw background color
        if not isDarkTheme():
            gradient.setColorAt(0, QColor(207, 216, 228, 255))
            gradient.setColorAt(1, QColor(207, 216, 228, 0))
        else:
            gradient.setColorAt(0, QColor(0, 0, 0, 255))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.fillPath(path, QBrush(gradient))

        # draw banner image
        pixmap = self.banner.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        painter.fillPath(path, QBrush(pixmap))


class HomeInterface(ScrollArea):
    """ Home interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.banner = BannerWidget(self)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        self.http = HTTPAPI()

        self.__initWidget()
        # self.loadSamples()

    def __initWidget(self):
        self.view.setObjectName('view')
        self.setObjectName('homeInterface')
        StyleSheet.HOME_INTERFACE.apply(self)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 36)
        self.vBoxLayout.setSpacing(40)
        self.vBoxLayout.addWidget(self.banner)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        menuLayout = QHBoxLayout()

        self.apiControlBtn = PushButton(FIF.PLAY, self.tr("Start API"))
        self.apiControlBtn.clicked.connect(self.api_control)

        self.openModelBtn = PushButton(FIF.FOLDER, self.tr("Open Models"))
        self.openModelBtn.clicked.connect(lambda: os.startfile(cfg.model_dir.value))
        self.openAudioBtn = PushButton(FIF.MUSIC_FOLDER, self.tr("Open Audio"))
        self.openAudioBtn.clicked.connect(lambda: os.startfile(cfg.output_dir.value))
        menuLayout.addWidget(self.apiControlBtn)
        menuLayout.addWidget(self.openModelBtn)
        menuLayout.addWidget(self.openAudioBtn)
        self.vBoxLayout.addLayout(menuLayout)
        if cfg.get(cfg.api_autostart):
            self.api_control()
        # if cfg.get(cfg.):

    def api_control(self):
        """ api control """
        if HTTPAPI().api_running:
            HTTPAPI().stop_api()
            logger.info("API stopped")
            self.apiControlBtn.setText(self.tr("Start API"))
            self.apiControlBtn.setIcon(FIF.PLAY)
        else:
            HTTPAPI().start_api()
            logger.info("API started")
            self.apiControlBtn.setText(self.tr("Stop API"))
            self.apiControlBtn.setIcon(FIF.PAUSE)

    def loadSamples(self):
        """ load samples """
        # basic input samples
        basicInputView = SampleCardView(
            self.tr("Folder"), self.view)
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Button.png",
            title=self.tr("Audio"),
            content=self.tr(
                "Generated audio directory."),
            routeKey="basicInputInterface",
            index=0
        )
        basicInputView.addSampleCard(
            icon=":/gallery/images/controls/Checkbox.png",
            title=self.tr("Configure"),
            content=self.tr("Configuration files directory"),
            routeKey="basicInputInterface",
            index=8
        )

        self.vBoxLayout.addWidget(basicInputView)
