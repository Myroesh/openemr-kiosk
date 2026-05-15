from google import genai
from config import Config


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