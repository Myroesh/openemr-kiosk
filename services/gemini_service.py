import json
import re

from google import genai

from config import Config
from services.validation_service import ALLOWED_CONSULTATION_REASONS


DEFAULT_CONSULTATION_REASON = "Sesión"


class GeminiService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY no está configurada en .env")

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = Config.GEMINI_MODEL

    def test_connection(self):
        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                "Responde solamente con esta frase exacta: "
                "Gemini conectado correctamente"
            ),
        )

        return response.text.strip()

    @staticmethod
    def _strip_markdown_json(text):
        text = str(text or "").strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()

        return text

    @staticmethod
    def _fallback_result(raw_text="", error=None):
        return {
            "status": "fallback",
            "reason": DEFAULT_CONSULTATION_REASON,
            "fallback_used": True,
            "raw_response": raw_text or "",
            "error": str(error) if error else None,
        }

    def classify_consultation_reason(self, user_text):
        """
        Clasifica un texto libre dentro del catálogo cerrado de motivos.

        Gemini no decide acciones, no escribe en OpenEMR y no puede devolver
        motivos fuera del catálogo permitido. Si falla, se usa fallback seguro.
        """

        user_text = str(user_text or "").strip()

        if not user_text:
            return self._fallback_result(error="Texto vacío")

        allowed_reasons_text = "\n".join(
            f"- {reason}" for reason in ALLOWED_CONSULTATION_REASONS
        )

        prompt = f"""
Eres un clasificador estricto para un kiosko de recepción clínica.

Tu tarea es clasificar el texto del usuario en UNA sola de estas opciones permitidas:

{allowed_reasons_text}

Reglas obligatorias:
- No inventes opciones nuevas.
- No expliques.
- No hagas diagnóstico.
- No des recomendaciones clínicas.
- Si el texto es ambiguo, usa "Sesión".
- Responde únicamente en JSON válido.
- El campo "reason" debe ser exactamente una de las opciones permitidas.
- El campo "confidence" debe ser "high", "medium" o "low".

Texto del usuario:
{user_text}

Formato exacto:
{{"reason": "Sesión", "confidence": "low"}}
""".strip()

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            raw_text = response.text.strip()
            cleaned_text = self._strip_markdown_json(raw_text)
            payload = json.loads(cleaned_text)

            reason = str(payload.get("reason") or "").strip()
            confidence = str(payload.get("confidence") or "low").strip().lower()

            if reason not in ALLOWED_CONSULTATION_REASONS:
                return self._fallback_result(
                    raw_text=raw_text,
                    error=f"Motivo fuera de catálogo: {reason}",
                )

            if confidence not in ("high", "medium", "low"):
                confidence = "low"

            return {
                "status": "ok",
                "reason": reason,
                "confidence": confidence,
                "fallback_used": False,
                "raw_response": raw_text,
                "error": None,
            }

        except Exception as exc:
            return self._fallback_result(error=exc)