import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
MODEL = "openai/gpt-oss-120b"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise HTTPException(status_code=503, detail="GROQ_API_KEY tanımlı değil. .env dosyasını kontrol edin.")
        _client = Groq(api_key=key)
    return _client


class LiveContext(BaseModel):
    date: Optional[str] = None
    mission_hours: Optional[float] = None
    illumination_pct: Optional[float] = None
    earth_visibility_pct: Optional[float] = None
    longest_daylight_h: Optional[float] = None
    verdict: Optional[str] = None


class KodiChatRequest(BaseModel):
    message: str
    selected_site_id: Optional[str] = None
    lang: str = "tr"
    live: Optional[LiveContext] = None


def read_json(name):
    path = OUTPUT_DIR / name
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_sites():
    sites = read_json("sites.json")
    if sites is None:
        raise HTTPException(status_code=404, detail="output/sites.json bulunamadı.")
    details = read_json("sites_detailed_report.json") or []
    by_id = {d["id"]: d for d in details}
    keys = ("verified", "mean_slope", "pct_under_5", "pct_under_10",
            "largest_flat_area_km2", "elevation_min", "elevation_max")
    merged = []
    for s in sites:
        item = dict(s)
        d = by_id.get(s["id"])
        if d:
            item["terrain"] = {k: d[k] for k in keys if k in d}
        merged.append(item)
    return merged


def build_system_prompt(lang):
    answer_lang = "English" if lang == "en" else "Turkish"
    return (
        "You are KODI, the friendly astronaut mascot of the LUNA Navigator project. "
        "You help users and judges compare Artemis III candidate landing regions at the lunar South Pole. "
        f"Always answer in {answer_lang}, in at most 120 words, in a friendly but technical tone.\n"
        "Rules:\n"
        "1. Use ONLY the data given below. Never invent numbers, dates or facts. If the data does not contain the answer, say so.\n"
        "2. Slope and terrain values come from NASA LOLA data (80 m/pixel, 15x15 km window average).\n"
        "3. The fields 'horizon' and 'ph' and the live illumination / Earth visibility percentages come from the interface's "
        "simplified prototype model, not from real SPICE calculations. Say that when you quote them.\n"
        "4. Regions with verified=false have preliminary coordinates. Mention it when relevant.\n"
        "5. This is not an operational or safety-certified tool.\n"
    )


@app.post("/api/kodi-chat")
async def kodi_chat(req: KodiChatRequest):
    sites = load_sites()
    target = None
    if req.selected_site_id:
        target = next((s for s in sites if s["id"] == req.selected_site_id), None)

    context = "Candidate regions:\n" + json.dumps(sites, ensure_ascii=False, indent=2)
    if target:
        context += "\n\nCurrently selected region:\n" + json.dumps(target, ensure_ascii=False, indent=2)
    if req.live:
        context += "\n\nLive values on the user's screen (prototype model):\n" + json.dumps(req.live.model_dump(exclude_none=True), ensure_ascii=False, indent=2)

    try:
        completion = get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": build_system_prompt(req.lang) + "\n" + context},
                {"role": "user", "content": req.message},
            ],
            temperature=0.3,
            max_tokens=700,
        )
        reply = completion.choices[0].message.content
    except HTTPException:
        raise
    except Exception as e:
        print("Groq error:", repr(e))
        raise HTTPException(status_code=502, detail="KODI şu an yanıt veremiyor.")

    return {"status": "success", "kodi_reply": reply, "active_site": target}
