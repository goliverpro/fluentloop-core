from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response

from app.middleware.auth import get_current_user
from app.models import TtsRequest

router = APIRouter()

ALLOWED_AUDIO_TYPES = {
    "audio/wav", "audio/wave", "audio/webm", "audio/ogg",
    "audio/mp4", "audio/mpeg", "audio/x-wav",
}


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    try:
        from app.services.speech import transcribe_audio
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech service not available",
        )

    audio_bytes = await audio.read()
    try:
        result = transcribe_audio(audio_bytes, audio.filename or "audio.wav")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Transcription failed: {str(e)}",
        )
    return result


@router.post("/tts")
async def text_to_speech(body: TtsRequest, current_user=Depends(get_current_user)):
    try:
        from app.services.speech import generate_tts
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TTS service not available",
        )

    try:
        audio_bytes = generate_tts(body.text, body.voice)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"TTS failed: {str(e)}",
        )

    return Response(content=audio_bytes, media_type="audio/mpeg")
