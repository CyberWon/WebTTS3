import asyncio
import json
from pathlib import Path

import ChatTTS

from PySide6.QtCore import QObject

from WebTTS3.app.common.audio import load_audio
from WebTTS3.app.common.config import cfg
import torch
import torchaudio

from WebTTS3.app.common.Singleton import Singleton
from loguru import logger
import tempfile, os


@Singleton
class ChatTTSEngine(QObject):
    def __init__(self):
        super().__init__()
        self.chat = ChatTTS.Chat()
        self.chat.load(custom_path=cfg.get(cfg.chattts_model), source="custom")
        self.model_dir = os.path.join(cfg.model_dir.value, "ChatTTS")
        os.makedirs(self.model_dir, exist_ok=True)
        self.speaker = {}

    def get_speaker(self, name=None, infer_code=None):
        if name:
            try:
                if not self.speaker.get(name):
                    with open(os.path.join(self.model_dir, f"{name}.json"), encoding="utf-8") as f:
                        data = json.load(f)
                        self.speaker[name] = data
                if self.speaker.get(name, {}).get("emb"):
                    infer_code.spk_emb = self.speaker[name]['emb']
                    return infer_code
                elif self.speaker.get(name, {}).get("smp"):
                    infer_code.spk_smp = self.speaker[name]['smp']
                    infer_code.txt_smp = self.speaker[name]['text']
                    return infer_code
            except Exception as e:
                logger.error(e)
                infer_code.spk_emb = self.chat.sample_random_speaker()
        else:
            infer_code.spk_emb = self.chat.sample_random_speaker()
        return infer_code

    async def infer(self, params: dict) -> dict:
        params_infer_code = ChatTTS.Chat.InferCodeParams(
            temperature=params['temperature'],  # using custom temperature
            top_P=params['top_p'],  # top P decode
            top_K=params['top_k'],  # top K decode
            manual_seed=None if params.get("seed") == -1 else params.get("seed"),
        )

        if params.get("ref_wav_path"):
            logger.debug(f"优先使用参考音频：{params.get('ref_wav_path')}")
            # 优先使用参考音频
            sample_audio = load_audio(params["ref_wav_path"], 24000)
            params["spk"] = None
            params_infer_code.txt_smp = params.get("prompt_text")
            params_infer_code.spk_smp = self.chat.sample_audio_speaker(sample_audio)
            del sample_audio
        else:
            params_infer_code = self.get_speaker(params.get('spk'),infer_code=params_infer_code)

        def engine_infer():
            params_refine_text = ChatTTS.Chat.RefineTextParams(
                prompt='[oral_2][laugh_0][break_6]',
            )

            wavs = self.chat.infer(params["text"], params_refine_text=params_refine_text,
                                   params_infer_code=params_infer_code, skip_refine_text=True)

            wavs_path = []

            for i in range(len(wavs)):
                wav_path = tempfile.mktemp(".wav", dir=cfg.output_dir.value)
                wavs_path.append(wav_path)
                logger.debug(f"保存wav:{wav_path}")
                emb_path = wav_path.replace('.wav', '.json')
                if params_infer_code.spk_emb:
                    with open(emb_path, 'w') as f:
                        json.dump({"emb": params_infer_code.spk_emb}, f, indent=4)
                elif params_infer_code.spk_smp:
                    with open(emb_path, 'w') as f:
                        json.dump({"smp": params_infer_code.spk_smp, "text": params_infer_code.txt_smp}, f, indent=4)
                try:
                    torchaudio.save(wav_path, torch.from_numpy(wavs[i]).unsqueeze(0), 24000)
                except:
                    torchaudio.save(wav_path, torch.from_numpy(wavs[i]), 24000)
            return wavs_path

        wavs_path = await asyncio.to_thread(engine_infer)
        if len(wavs_path) > 1:
            # todo: pass
            logger.debug(f"合并")
        return [1, wavs_path[0]]
