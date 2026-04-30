"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_HUB_ID = "leonanluppi/bug_to_user_story_v1"
PROMPT_LOCAL_PATH = Path("prompts/bug_to_user_story_v1.yml")
PROMPT_KEY = "bug_to_user_story_v1"


def _extract_message_template(message: Any) -> str:
    """Extrai o texto de templates de mensagem do LangChain."""
    prompt = getattr(message, "prompt", None)
    if prompt is not None:
        return getattr(prompt, "template", str(prompt))

    return getattr(message, "template", getattr(message, "content", str(message)))


def _extract_message_role(message: Any) -> str:
    """Normaliza a role da mensagem para o formato usado no YAML."""
    class_name = message.__class__.__name__.lower()

    if "system" in class_name:
        return "system"
    if "human" in class_name:
        return "user"
    if "ai" in class_name:
        return "assistant"

    return "user"


def _prompt_to_yaml_data(prompt: Any) -> dict:
    """
    Converte o objeto retornado pelo LangSmith Hub para a estrutura local.

    O Hub pode retornar ChatPromptTemplate ou PromptTemplate dependendo de como
    o prompt foi publicado, então a extração precisa tratar ambos os formatos.
    """
    prompt_metadata = getattr(prompt, "metadata", None) or {}
    prompt_tags = getattr(prompt, "tags", None) or ["bug-analysis", "user-story", "product-management"]

    prompt_data = {
        "description": prompt_metadata.get(
            "description",
            "Prompt para converter relatos de bugs em User Stories"
        ),
        "version": "v1",
        "tags": prompt_tags,
        "langsmith_hub_id": PROMPT_HUB_ID,
    }

    if isinstance(prompt, ChatPromptTemplate):
        messages = []

        for message in prompt.messages:
            messages.append({
                "role": _extract_message_role(message),
                "template": _extract_message_template(message),
            })

        system_messages = [
            message["template"]
            for message in messages
            if message["role"] == "system"
        ]
        user_messages = [
            message["template"]
            for message in messages
            if message["role"] == "user"
        ]

        prompt_data["system_prompt"] = "\n\n".join(system_messages).strip()
        prompt_data["user_prompt"] = "\n\n".join(user_messages).strip()

        if len(messages) > 2:
            prompt_data["messages"] = messages

        return {PROMPT_KEY: prompt_data}

    if isinstance(prompt, PromptTemplate):
        prompt_data["system_prompt"] = prompt.template
        prompt_data["user_prompt"] = "{bug_report}"

        return {PROMPT_KEY: prompt_data}

    raise TypeError(f"Tipo de prompt não suportado: {type(prompt).__name__}")


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt inicial do LangSmith Hub e salva em YAML.

    Returns:
        True se o pull e a gravação local forem concluídos com sucesso.
    """
    print_section_header("Pull do prompt inicial do LangSmith")

    try:
        print(f"Fazendo pull de: {PROMPT_HUB_ID}")
        prompt = hub.pull(
            PROMPT_HUB_ID,
            api_url=os.getenv("LANGSMITH_ENDPOINT"),
            api_key=os.getenv("LANGSMITH_API_KEY"),
        )

        prompt_yaml = _prompt_to_yaml_data(prompt)

        if save_yaml(prompt_yaml, str(PROMPT_LOCAL_PATH)):
            print(f"✅ Prompt salvo em: {PROMPT_LOCAL_PATH}")
            return True

        return False
    except Exception as exc:
        print(f"❌ Erro ao fazer pull do prompt: {exc}")
        return False


def main():
    """Função principal"""
    required_vars = [
        "LANGSMITH_ENDPOINT",
        "LANGSMITH_API_KEY",
    ]

    if not check_env_vars(required_vars):
        return 1

    if pull_prompts_from_langsmith():
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
