import sys, os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(sys.path[0]))
sys.path.insert(0, os.path.dirname(sys.path[0]))

from PySide6 import QtAsyncio
from PySide6.QtCore import QThread, QObject, Slot, Signal, Property, QEventLoop
from PySide6.QtGui import QGuiApplication
from fastapi import FastAPI, Depends, HTTPException
import uvicorn
import asyncio
from loguru import logger

from starlette.responses import FileResponse, Response

from WebTTS3.tts.api_models import Params
from WebTTS3.tts.infer import TTSInfer

from fastapi.middleware.cors import CORSMiddleware
from WebTTS3.app.common.config import cfg, VERSION
from WebTTS3.app.common.Singleton import Singleton
from WebTTS3.app.common.audio import reSize
from contextlib import asynccontextmanager

tts_infer: TTSInfer = None
tts_config = {}
output_dir = cfg.get(cfg.output_dir)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup 逻辑
    global tts_infer, output_dir
    output_dir = cfg.get(cfg.output_dir)  # 获取配置中的输出目录
    tts_infer = TTSInfer()  # 实例化 TTSInfer 对象
    await load_tts_config()  # 加载 TTS 配置
    logger.debug("初始化完成")
    try:
        yield  # 应用启动并运行
    finally:
        # shutdown 逻辑（如需清理资源可在此添加）
        pass


app = FastAPI(
    title="WebTTS3",
    version=VERSION,
    summary=f"WebTTS3是CyberWon开发的一款集成多家语音合成大模型的软件。开源协议为AGPLV3，请注意。禁止商用和倒卖。",
    terms_of_service="https://tts.berstar.cn",
    contact={
        "name": "CyberWon",
        "url": "https://tts.berstar.cn",
        "email": "mail@berstar.cn",
    },
    license_info={
        "name": "AGPLV3",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
    lifespan=lifespan,
)

dependencies = None
origins = ["*"]


async def load_tts_config():
    global tts_config
    _config = {"speaker": {}}
    for engine in tts_infer._engine:
        engine_config = await tts_infer.get_config(engine)
        if engine_config is None:
            logger.error(f"{engine} config is None")
            continue
        new_config = {}
        for spk in engine_config:
            new_config[f'{spk}__{engine}'] = engine_config[spk]
        _config['speaker'].update(new_config)
    tts_config = _config


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/config')
async def get_config():
    await load_tts_config()
    return tts_config


async def handle(params: Params):
    if params.spk:
        spk_info = params.spk.split("__")
    else:
        spk_info = [0, "ChatTTS"]
    if len(spk_info) == 2:
        params.spk = spk_info[0]
        params.engine = spk_info[1]
    if params.text is None:
        params.text = "欢迎使用WebTTS,祝您使用愉快。"
    try:
        code, audio = await tts_infer.infer(params.dict(), params.engine)
    except Exception as e:
        return {"code": 2, "msg": f"{e}"}
    if code == 1:
        if params.local:
            return {"code": code, "file": audio, "url": "", "data": audio}
        if params.format == "wav":
            return FileResponse(audio)
        if params.engine == "ChatTTS":
            return FileResponse(reSize(audio, hz=24000, suffix="ogg"))
        return FileResponse(reSize(audio, suffix="ogg"))
    else:
        return {"code": code, "msg": audio}


@app.get("/", description="TTS GET接口", tags=["语音合成"], dependencies=dependencies)
async def tts_get(params: Params = Depends(Params)):
    return await handle(params)


@app.post("/", description="TTS GET接口", tags=["语音合成"], dependencies=dependencies)
async def tts_post(params: Params):
    return await handle(params)


async def start_api():
    timeout = cfg.get(cfg.timeout)
    if timeout == 0:
        timeout = 600
    config = uvicorn.Config(app, host=cfg.get(cfg.host), port=cfg.get(cfg.port), timeout_keep_alive=timeout)
    server = uvicorn.Server(config)
    await server.serve()


class HTTPAPIThread(QThread):
    def __init__(self):
        super().__init__()
        self.host = cfg.get(cfg.host)
        self.port = cfg.get(cfg.port)
        self.loop = None
        self.server = None

    async def start_server(self):
        timeout = cfg.get(cfg.timeout)
        if timeout == 0:
            timeout = 600
        config = uvicorn.Config(app, host=self.host, port=self.port, timeout_keep_alive=timeout)
        self.server = uvicorn.Server(config)
        await self.server.serve()

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.start_server())
        except Exception as e:
            logger.error(e)

    def stop(self):
        if self.server:
            self.server.should_exit = True
        self.quit()


@Singleton
class HTTPAPI(QObject):
    statusChanged = Signal(bool)

    def __init__(self):
        QObject.__init__(self, QGuiApplication.instance())
        self.http_api = None
        self.api_running = False

    @Property(bool, notify=statusChanged)
    def status(self):
        return self.api_running

    @status.setter
    def status(self, value):
        self.api_running = value
        self.statusChanged.emit(value)

    @Slot(result=dict)
    def start_api(self):
        if not self.api_running:
            self.http_api = HTTPAPIThread()
            self.http_api.start()
            logger.info("api started")
            self.status = True
        return {"code": 0, "msg": "api started"}

    @Slot(result=dict)
    def stop_api(self):
        if self.http_api:
            self.http_api.stop()
            self.status = False
        return {"code": 0, "msg": "api stopped"}


if __name__ == "__main__":
    # http_api = HTTPAPIThread()
    # http_api.start()
    # QtAsyncio.run()
    asyncio.run(HTTPAPIThread().start_server())
