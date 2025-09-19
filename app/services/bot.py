#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame, EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.gemini_multimodal_live.gemini import (
    GeminiMultimodalLiveLLMService,
    InputParams,
    GeminiVADParams,
    GeminiMultimodalModalities
)
from pipecat.services.gemini_multimodal_live.events import (
    StartSensitivity,
    EndSensitivity
)
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transcriptions.language import Language
from simli import SimliConfig
from pipecat.services.simli.video import SimliVideoService
from datetime import datetime
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
import aiohttp
import json
from app.schemas import InterviewResponse
from pipecat.transports.services.daily import DailyTransport, DailyParams
# Load environment variables

logger.add(
    "pipecat_debug.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}"
)
# We store functions so objects (e.g. SileroVADAnalyzer) don't get
# instantiated. The function will be called when the desired transport gets
# selected.
datetime_function = FunctionSchema(
    name="get_current_datetime",
    description="Get the current datetime so you can calculate time left for interview",
    properties={},
    required=[]
)
stop_interview = FunctionSchema(
    name="stop_interview",
    description="Stop the interview",
    properties={
        "report": {
            "type": "string",
            "description": "Report of the interview for HR"
        }
    },
    required=["report"]
)
tools = ToolsSchema(standard_tools=[datetime_function, stop_interview])
async def get_current_datetime(params: FunctionCallParams):
    # Fetch weather data from your API
    datetime_data = {"datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    await params.result_callback(datetime_data)
# Create a tools schema with your functions
def _make_stop_interview(transport: DailyTransport, api_base_url: str, auth_headers: dict, interview_id: int):
    async def _stop_interview(params: FunctionCallParams):
        try:
            args = params.arguments or {}
            report = args.get("report")

            payload = {"end_date": datetime.now().isoformat()}
            if report:
                payload["summary"] = report
            logger.info(f"Interview {interview_id} stopped with report: {report}")
            async with aiohttp.ClientSession() as session:
                # Save summary/end_date via API
                url = f"{api_base_url}/interviews/{interview_id}"
                async with session.put(url, json=payload, headers=auth_headers) as resp:
                    resp_text = await resp.text()
                    if resp.status >= 400:
                        logger.error(f"Failed to update interview {interview_id}: {resp.status} {resp_text}")
                        await params.result_callback({"ok": False, "status": resp.status, "body": resp_text})
                    else:
                        logger.info(f"Interview {interview_id} updated successfully")
                        # Disconnect WebRTC session
                        try:
                            await transport.output().stop(EndFrame())
                            logger.info("Transport disconnected")
                        except Exception as e:
                            logger.error(f"Error disconnecting transport: {e}")
                        await params.result_callback({"ok": True})
        except Exception as e:
            logger.exception("Unhandled error in stop_interview")
            try:
                await params.result_callback({"ok": False, "error": str(e)})
            except Exception:
                pass
    return _stop_interview

async def run_bot(webrtc_connection, interview_id, room_url, token):
    logger.info(f"Starting bot")
    pipecat_transport = DailyTransport(
        room_url=room_url,
        token=token,
        params=DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        video_out_enabled=True,
        video_out_is_live=True,
        video_out_width=632,
        video_out_height=632,
        # set stop_secs to something roughly similar to the internal setting
        # of the Multimodal Live api, just to align events.
        vad_analyzer=None
    ),
    )

    # Configure API base and auth for server-to-server calls
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_token = None
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{api_base_url}/auth/login", json={"username": f"{os.getenv('HR_USERNAME')}", "password": f"{os.getenv('HR_PASSWORD')}"}) as response:
            if response.status == 200:
                api_token = await response.json()
                api_token = api_token["access_token"]
            else:
                logger.error(f"Failed to get API token. Status code: {response.status}")
    auth_headers = {"Authorization": f"Bearer {api_token}"} if api_token else {}

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/interviews/{interview_id}", headers=auth_headers) as response:
            if response.status == 200:
                interview_data = await response.json()
                logger.info(f"Interview data: {interview_data}")
            else:
                logger.error(f"Failed to get interview data. Status code: {response.status}")
    interview = InterviewResponse.model_validate(interview_data)
    vacancy = interview.vacancy
    resume = interview.resume
    # Получаем JSON-дружелюбные dict, чтобы корректно сериализовать Enum и datetime
    vacancy_dict = vacancy.model_dump(
        mode='json',
        exclude={"id", "original_url", "creator_id", "hr_id", "auto_interview_enabled", "created_at", "updated_at", "status"}
    )
    resume_dict = resume.model_dump(
        mode='json',
        exclude={"id", "user_id", "vacancy_id", "file_path", "original_filename", "uploaded_at", "processed", "uploaded_by_hr", "hidden_for_hr", "updated_at", "status", "user"}
    )

    vacancy_data = json.dumps(vacancy_dict, ensure_ascii=False, indent=2)
    resume_data = json.dumps(resume_dict, ensure_ascii=False, indent=2)
    
    logger.info(f"Vacancy data: {vacancy_data}")
    logger.info(f"Resume data: {resume_data}")
    system_instruction = f"""
Ты — Александра, продвинутый HR-интервьюер.

**Задача:** Провести структурированное интервью на **русском языке**, соблюдая этические нормы (без дискриминационных вопросов). Твоя роль — оценить кандидата и подготовить отчет для HR-менеджера, **а не принимать решение о найме**.
Текущее время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

### **План Действий**

**1. Внутренний анализ (перед первым вопросом):**
* Выдели из вакансии 5-7 ключевых компетенций.
* Сопоставь их с резюме, определи главные темы для проверки.

**2. Проведение интервью (взаимодействие с кандидатом):**
* **Структура по времени:** Придерживайся плана: Вступление (~5%), Основные вопросы (~70%), Вопросы кандидата (~15%), Завершение (~10%).
* **Начало:** Кратко представься и озвучь план беседы.
* **Диалог:** Задавай по **одному** вопросу за раз. Если ответ неполный — задавай уточняющие вопросы.
* **Завершение:** Будь нейтрален. Поблагодари, озвучь следующие шаги (например, «Мы свяжемся с вами в течение N дней») и пожелай хорошего дня. Не давай никаких намеков на решение.

**3. Итоговый отчет (для HR-менеджера):**
* **Оценка по компетенциям:**
    * `[Компетенция]`: `[Подтверждена / Частично / Не подтверждена]` — `[Краткое обоснование]`
* **Сильные стороны:** (список 2-3)
* **Риски / Зоны роста:** (список 1-2)
* **Рекомендация:** `[Рекомендовать / Рассмотреть / Не рекомендовать]` с четкой аргументацией.
Пожалуйста, произноси числительные на русском языке, для этого можешь перевести их в письменную форму, например, 3 - "три
    """
    context = OpenAILLMContext(
    messages=[
        {
            "role": "system",
            "content": system_instruction
        },
        {
            "role": "user",
            "content": f"""**Входные данные о кандидате:**
* **Вакансия: {vacancy_data}**
* **Резюме: {resume_data}**
* **Время (минут):5**. Поприветствуй кандидата и начни собеседование."""
        }
    ])
    llm = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        system_instruction=system_instruction,
        voice_id="Aoede",  # Aoede, Charon, Fenrir, Kore, Puck
        language=Language.RU_RU,
        vad=GeminiVADParams(
                start_sensitivity=StartSensitivity.HIGH,    # Быстро детектируем начало речи
                end_sensitivity=EndSensitivity.LOW,         # Даем больше времени на паузы
                prefix_padding_ms=500,                      # Увеличиваем буфер до речи
                silence_duration_ms=2000,                   # Увеличиваем время тишины до 2 сек
            ),
        tools=tools,
    )
    context_aggregator = llm.create_context_aggregator(context)
    llm.register_function(
    "get_current_datetime",
    get_current_datetime,
    cancel_on_interruption=True,  # Cancel if user interrupts (default: True)
    )
    # Register stop_interview tool to allow LLM to save summary and end the session
    llm.register_function(
        "stop_interview",
        _make_stop_interview(pipecat_transport, api_base_url, auth_headers, interview_id),
        cancel_on_interruption=True,
    )
    simli = SimliVideoService(
        SimliConfig(
            apiKey=os.getenv("SIMLI_API_KEY"),
            faceId=os.getenv("SIMLI_FACE_ID"),
            handleSilence=True,
            maxSessionLength=300,
            maxIdleTime=30,
        ),
        use_turn_server=True,
        latency_interval=0
    )
    # Build the pipeline
    pipeline = Pipeline(
        [
            pipecat_transport.input(),
            context_aggregator.user(),
            llm,
            simli,
            pipecat_transport.output(),
            context_aggregator.assistant()
        ]
    )

    # Configure the pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        )
    )

    # Handle client connection event
    @pipecat_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # Kick off the conversation.
        await task.queue_frames(
            [
                LLMRunFrame()
            ]
        )

    # Handle client disconnection events
    @pipecat_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    # Run the pipeline
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)