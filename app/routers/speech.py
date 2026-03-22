from fastapi import APIRouter, Depends, UploadFile, File
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    # TODO: send to Azure Speech STT + Pronunciation Assessment
    raise NotImplementedError


@router.post("/tts")
async def text_to_speech(current_user=Depends(get_current_user)):
    # TODO: generate audio via OpenAI TTS, upload to Supabase Storage
    raise NotImplementedError
