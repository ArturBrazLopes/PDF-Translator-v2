"""
config/settings.py — Configurações centralizadas do projeto.
Qualquer mudança de idioma, provider ou modelo começa aqui.
"""

# Idiomas disponíveis para tradução
# Chave: nome exibido na interface | Valor: nome em inglês para o prompt da IA
LANGUAGES: dict[str, str] = {
    "Portuguese": "Portuguese (Brazil)",
    "English": "English",
    "Spanish": "Spanish",
    "French": "French",
    "German": "German",
    "Italian": "Italian",
    "Japanese": "Japanese",
    "Chinese": "Chinese (Simplified)",
    "Russian": "Russian",
    "Arabic": "Arabic",
}

# Provedores de IA disponíveis
PROVIDERS: dict[str, dict] = {
    "Groq": {
        "label": "Groq",
        "needs_key": True,
        "env_key": "GROQ_API_KEY",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
    },
    "Gemini (alfa)(not recommended)": {
        "label": "Gemini (alfa)(not recommended)",
        "needs_key": True,
        "env_key": "GEMINI_API_KEY",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
    },
    "OpenRouter (alfa)(not recommended)": {
        "label": "OpenRouter (alfa)(not recommended)",
        "needs_key": True,
        "env_key": "OPENROUTER_API_KEY",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
            "meta-llama/llama-4-maverick:free",
            "qwen/qwen3-235b-a22b:free",
            "openrouter/auto",
        ],
    },
    "Ollama": {
        "label": "Ollama (Local)",
        "needs_key": False,
        "env_key": None,
        "models": [
            "translategemma:latest",
            "gemma4:e4b",
            "llama3.3:8b",
            "llama3.2:3b",
            "phi4-mini",
            "qwen2.5:7b",
            "mistral",
        ],
    },
}

# Separador usado na tradução em batch
BLOCK_SEPARATOR = "|||BLOCK|||"

# Configurações do PDF gerado
PDF_MARGIN_CM   = 2.5
PDF_BODY_SIZE   = 11
PDF_TITLE_SIZE  = 13
PDF_BODY_LEAD   = 17
PDF_TITLE_LEAD  = 18