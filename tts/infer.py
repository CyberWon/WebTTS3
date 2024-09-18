import json
import os.path
import pathlib
import re
import tempfile
import traceback

from PySide6.QtCore import QObject, Signal, Slot, QDir
from pydub import AudioSegment
import copy

from qasync import asyncSlot

from WebTTS3.tts.api_models import Params

pinyin = None
from loguru import logger
from WebTTS3.app.common.config import cfg
from WebTTS3.tts import load_ext


class BaseInfer(QObject):
    configChanged = Signal(dict, str, arguments=["config", "type"])
    inferResult = Signal(int, str, arguments=["code", "data"])

    def clean_filename(self, filename):
        # 特殊字符列表，可以根据需要添加或删除字符
        special_chars = ['/', '\\', "\n", ':', '*', '?', '"', '<', '>', '|', '\0']

        # 使用字符串的translate方法去除特殊字符
        clean_name = ''.join(char for char in filename if char not in special_chars)

        return clean_name

    def onInferResult(self, code, data):
        logger.debug(f'Infer result: {code} {data}')
        self.inferResult.emit(code, data)

    async def get_config(self):
        return {}

    async def infer(self, params: Params):
        return {}

    def synthesis(self):
        return {}


class ChatTTSInfer(BaseInfer):
    def __init__(self):
        super().__init__()
        self.config = {}
        from WebTTS3.tts.engine.e_chattts import ChatTTSEngine
        self.engine = ChatTTSEngine()

    async def get_config(self):
        data = {"": {}}
        model_dir = os.path.join(cfg.model_dir.value, "ChatTTS")
        os.makedirs(model_dir, exist_ok=True)
        for file_info in QDir(model_dir).entryInfoList(QDir.NoDotAndDotDot | QDir.Files):
            if file_info.fileName().endswith(".json"):
                data[file_info.fileName()[:-5]] = {}
        self.configChanged.emit(data, "ChatTTS")
        return data

    async def infer(self, params: dict):
        return await self.engine.infer(params=params)


class TTSInfer(QObject):
    configChanged = Signal(dict, arguments=["config"])
    inferResult = Signal(int, str, arguments=["code", "data"])
    sampleDataChanged = Signal()
    durationChanged = Signal()
    phonemeList = Signal(list)

    def __init__(self):
        super().__init__()
        self._voicers = {}
        self._speakers = {}
        self._duration = 0

        self._engine = {
        }
        if cfg.get(cfg.chattts_enable):
            logger.debug("ChatTTS 引擎已启用")
            self._engine["ChatTTS"] = ChatTTSInfer()
        for engineName in self._engine:
            if self._engine[engineName]:
                self._engine[engineName].configChanged.connect(self.parseConfig)
                self._engine[engineName].inferResult.connect(self._inferResult)
                # self._engine[engineName].get_config()

    def _inferResult(self, code, data):
        self.inferResult.emit(code, data)

    def parseConfig(self, config: dict, engineName: str):
        # logger.debug(config.keys())
        self._voicers[engineName] = []
        self._speakers[engineName] = config
        for voicer in config:
            self._voicers[engineName].append(
                {
                    "name": voicer,
                    "avatar": config.get(voicer, {}).get("avatar", cfg.get(cfg.default_avatar)),
                    "desc": config.get(voicer, {}).get("desc", ""),
                    "engine": engineName
                }
            )
        self.configChanged.emit(config)

    async def get_config(self, engineName="Azure"):
        try:
            return await self._engine[engineName].get_config()
        except Exception as e:
            logger.error(f"{engineName}语音合成引擎没启用？")
            return {}

    @Slot(result=list)
    def engine(self):
        arr = []
        for _engine in self._engine:
            arr.append({"name": _engine, "speakers": len(self._speakers.get(_engine, {}).keys())})
        return arr

    @Slot(result=list)
    @Slot(str, str, result=list)
    def voicers(self, keyword=None, engineName="ChatTTS") -> list:
        if keyword:
            searchList = []
            for _, voicer in enumerate(self._voicers.get(engineName, [])):
                if keyword in voicer["name"]:
                    searchList.append(voicer)
            return searchList
        # logger.debug(f'voicers called: {keyword}, {engineName} result: {self._voicers.get(engineName, [])}')
        return self._voicers.get(engineName, [])

    async def infer(self, args, engineName):
        logger.debug(f'infer called: {engineName}, {args}')

        return await self._engine[engineName].infer(args)

    @Slot(str, str, result=list)
    def emotions(self, voicerName, engineName="Azure"):
        arr = []
        try:
            emotions = self._speakers[engineName].get(voicerName, {}).get("emotion", {})
            for _emotion in emotions:
                arr.append({"name": _emotion, "args": emotions.get(_emotion)})
            # logger.debug(f'emotions called: {voicerName}, {engineName} result: {arr}')
        except Exception as e:
            logger.error(f"{engineName} 引擎出现错误。{e}")
        return arr

    @Slot(str, str, result=list)
    def roles(self, voicerName, engineName="Azure"):
        roles = self._speakers[engineName].get(voicerName, {}).get("role", [])
        return roles

    @Slot(str, result=dict)
    def delete(self, path):
        # os.remove(path)
        logger.debug(f'delete called: {path}')
        if os.path.isfile(path):
            os.remove(path)
            return {"code": 0}
        else:
            return {"code": 1}

    def synthesis(self, args, engine="GPT-SoVITS", output_dir="None"):
        res = self._engine[engine].synthesis(args, output_dir=output_dir)
        return res


if __name__ == '__main__':
    pass
