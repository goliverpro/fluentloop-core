import azure.cognitiveservices.speech as speechsdk
from openai import OpenAI

from app.config import settings


def transcribe_audio(audio_bytes: bytes, filename: str) -> dict:
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    speech_config.speech_recognition_language = "en-US"

    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True,
    )

    audio_stream = speechsdk.audio.PushAudioInputStream()
    audio_stream.write(audio_bytes)
    audio_stream.close()
    audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )
    pronunciation_config.apply_to(recognizer)

    result = recognizer.recognize_once_async().get()

    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        return {"text": "", "words": []}

    pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
    words = []
    for i, word in enumerate(pronunciation_result.words):
        words.append({
            "word": word.word,
            "position": i,
            "accuracy_score": word.accuracy_score,
            "phoneme_feedback": None,
        })

    return {"text": result.text, "words": words}


def generate_tts(text: str, voice: str = "alloy") -> bytes:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    return response.content
