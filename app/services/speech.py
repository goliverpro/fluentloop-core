import io

from openai import OpenAI

from app.config import settings


def transcribe_audio(audio_bytes: bytes, filename: str) -> dict:
    # MVP: usa OpenAI Whisper para transcrição simples.
    # Não há score de pronúncia por palavra — campo "words" retorna vazio.
    #
    # EVOLUÇÃO → Azure Speech (quando implementar feedback de pronúncia):
    #   - Trocar este bloco pelo cliente azure.cognitiveservices.speech
    #   - Usar PronunciationAssessmentConfig com granularity=Phoneme
    #   - Preencher "words" com accuracy_score por palavra
    #   - Requer: AZURE_SPEECH_KEY + AZURE_SPEECH_REGION no .env
    #   - Dependência: azure-cognitiveservices-speech no requirements.txt
    #   - Ver implementação original em git history (commit antes de 2026-03-25)
    client = OpenAI(api_key=settings.openai_api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en",
    )
    return {"text": transcription.text, "words": []}


def generate_tts(text: str, voice: str = "alloy") -> bytes:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    return response.content
