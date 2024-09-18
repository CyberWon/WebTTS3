import sys, os

from PySide6.QtCore import QThread
from loguru import logger

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(sys.path[0]))
sys.path.insert(0, os.path.dirname(sys.path[0]))
from WebTTS3.app.common.config import cfg
import traceback


class LoadChatTTS(QThread):

    def run(self):
        try:
            from WebTTS3.tts.engine.e_chattts import ChatTTSEngine
            ChatTTSEngine()
        except Exception as e:
            traceback.print_exc()
            logger.error(f"ChatTTS 加载失败，配置的{cfg.chattts_model.value}有误。")


if cfg.get(cfg.chattts_enable):
    sys.path.append(cfg.get(cfg.chattts_dir))
    l = LoadChatTTS()
    l.run()
    logger.info("ChatTTS 加载完成")