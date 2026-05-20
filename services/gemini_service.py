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
    def _normalize_text(value):
        value = str(value or "").lower().strip()
        value = re.sub(r"\s+", " ", value)
        return value

    @staticmethod
    def _fallback_result(raw_text="", error=None):
        return {
            "status": "fallback",
            "reason": DEFAULT_CONSULTATION_REASON,
            "confidence": "low",
            "source": "fallback",
            "fallback_used": True,
            "raw_response": raw_text or "",
            "error": str(error) if error else None,
        }

    @staticmethod
    def _rule_result(reason, confidence="high"):
        return {
            "status": "ok",
            "reason": reason,
            "confidence": confidence,
            "source": "rules",
            "fallback_used": False,
            "raw_response": "",
            "error": None,
        }

    def _classify_by_rules(self, user_text):
        """
        Clasificación local barata antes de llamar Gemini.

        Si una frase es obvia, no gastamos tokens.
        """

        text = self._normalize_text(user_text)

        if not text:
            return None

        result_keywords = (
            "resultado",
            "resultados",
            "informe",
            "devolución",
            "devolucion",
            "reporte",
        )

        parent_keywords = (
            "papá",
            "papa",
            "mamá",
            "mama",
            "padre",
            "madre",
            "padres",
            "hijo",
            "hija",
            "mi niño",
            "mi niña",
            "mi hijo",
            "mi hija",
        )

        initial_keywords = (
            "primera vez",
            "primera consulta",
            "consulta inicial",
            "nuevo paciente",
            "soy nuevo",
            "soy nueva",
            "es nuevo",
            "es nueva",
        )

        test_keywords = (
            "test",
            "prueba",
            "pruebas",
            "evaluación",
            "evaluacion",
            "wisc",
            "tova",
            "nextplora",
            "batería",
            "bateria",
        )

        session_keywords = (
            "sesión",
            "sesion",
            "terapia",
            "cita",
            "seguimiento",
            "consulta de hoy",
        )

        if any(keyword in text for keyword in result_keywords):
            return self._rule_result("Revisión de resultados")

        if any(keyword in text for keyword in initial_keywords):
            return self._rule_result("Consulta Inicial")

        if any(keyword in text for keyword in parent_keywords):
            if any(word in text for word in ("hablar", "entrevista", "reunión", "reunion", "conversar")):
                return self._rule_result("Entrevista con los padres")

        if any(keyword in text for keyword in test_keywords):
            return self._rule_result("Test")

        if any(keyword in text for keyword in session_keywords):
            return self._rule_result("Sesión", confidence="medium")

        return None

    def classify_consultation_reason(self, user_text):
        """
        Clasifica un texto libre dentro del catálogo cerrado de motivos.

        Primero intenta reglas locales gratuitas.
        Si no hay clasificación clara, usa Gemini.
        Gemini no decide acciones, no escribe en OpenEMR y no puede devolver
        motivos fuera del catálogo permitido. Si falla, se usa fallback seguro.
        """

        user_text = str(user_text or "").strip()

        if not user_text:
            return self._fallback_result(error="Texto vacío")

        rule_result = self._classify_by_rules(user_text)
        if rule_result:
            return rule_result

        allowed_reasons_text = "\n".join(
            f"- {reason}" for reason in ALLOWED_CONSULTATION_REASONS
        )

        prompt = f"""
Eres un clasificador estricto para un kiosko de recepción clínica en un centro neuropscicológico llamado "centro neuropsicológico saavedra".

Tu tarea es clasificar el texto del usuario en UNA sola de estas opciones permitidas:

{allowed_reasons_text}

Ejemplos:
- "vengo a revisar mis resultados" => Revisión de resultados
- "me dijeron que venga por los resultados del test" => Revisión de resultados
- "es mi primera vez en el centro" => Consulta Inicial
- "quiero una primera consulta" => Consulta Inicial
- "tengo mi sesión de terapia" => Sesión
- "vengo a mi cita normal" => Sesión
- "vengo para evaluación" => Test
- "me toca prueba o test" => Test
- "soy la mamá y quiero hablar del caso de mi hijo" => Entrevista con los padres
- "soy el papá y quiero reunirme con la doctora" => Entrevista con los padres

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
                "source": "gemini",
                "fallback_used": False,
                "raw_response": raw_text,
                "error": None,
            }

        except Exception as exc:
            return self._fallback_result(error=exc)