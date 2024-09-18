# coding:utf-8
import os.path
import sys
from enum import Enum

from PySide6.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, __version__)


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """ Config of application """
    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # Material
    blurRadius = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())

    # ChatTTS
    chattts_dir = ConfigItem("ChatTTS", "chattts_dir", "repo/chattts", FolderValidator())
    chattts_model = ConfigItem("ChatTTS", "chattts_model", "base_model/chattts", FolderValidator())
    chattts_enable = ConfigItem("ChatTTS", "chattts_enable", False, BoolValidator(), restart=True)

    # TTS Default
    output_dir = ConfigItem("TTS", "output_dir", "TEMP", FolderValidator())
    api_autostart = ConfigItem("TTS", "api_autostart", False, BoolValidator(), restart=True)
    host = ConfigItem("TTS", "host", "0.0.0.0")
    port = ConfigItem("TTS", "port", 20080)
    timeout = ConfigItem("TTS", "timeout", 600)
    default_avatar = ConfigItem("TTS", "default_avatar", "")
    model_dir = ConfigItem("TTS", "model_dir", "models")


VOICER_AVATAR = ""
YEAR = 2024
AUTHOR = "CyberWon"
VERSION = "3.0.0"
HELP_URL = "https://yxi3w0wmgv2.feishu.cn/wiki/JilfwWyNRiTWlkkheeUck40qnaf"
REPO_URL = "https://github.com/CyberWon/WebTTS3"
EXAMPLE_URL = ""
FEEDBACK_URL = ""
RELEASE_URL = ""
ZH_SUPPORT_URL = ""
EN_SUPPORT_URL = ""

BUY_NOVEL_DUB = "https://gf.bilibili.com/item/detail/1108739091"
BUY_AI_DUB = "https://gf.bilibili.com/item/detail/1107363091"

cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('config/config.json', cfg)
