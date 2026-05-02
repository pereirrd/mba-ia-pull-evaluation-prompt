"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_LOCAL_PATH = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_VERSION = "v2"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data.get("user_prompt", "{bug_report}")),
        ])

        prompt_template.metadata = {
            "description": prompt_data.get("description", ""),
            "version": prompt_data.get("version", PROMPT_VERSION),
            "techniques_applied": prompt_data.get("techniques_applied", []),
            "source_file": PROMPT_LOCAL_PATH,
        }
        prompt_template.tags = prompt_data.get("tags", [])

        print(f"Fazendo push de: {prompt_name}")
        url = hub.push(
            prompt_name,
            prompt_template,
            api_url=os.getenv("LANGSMITH_ENDPOINT"),
            api_key=os.getenv("LANGSMITH_API_KEY"),
            new_repo_is_public=True,
            new_repo_description=prompt_data.get("description", ""),
            tags=prompt_data.get("tags", []),
        )

        print(f"✓ Prompt publicado com sucesso: {url}")
        print("✓ Visibilidade solicitada: público")
        return True
    except Exception as exc:
        print(f"❌ Erro ao publicar prompt '{prompt_name}': {exc}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    is_valid, errors = validate_prompt_structure(prompt_data)

    if prompt_data.get("version") != PROMPT_VERSION:
        errors.append(f"Versão esperada: {PROMPT_VERSION}")

    user_prompt = prompt_data.get("user_prompt", "").strip()
    if not user_prompt:
        errors.append("user_prompt está vazio")

    if "{bug_report}" not in user_prompt and "{bug_report}" not in prompt_data.get("system_prompt", ""):
        errors.append("Placeholder obrigatório '{bug_report}' não encontrado")

    tags = prompt_data.get("tags", [])
    if not isinstance(tags, list) or not tags:
        errors.append("tags deve ser uma lista não vazia")

    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list):
        errors.append("techniques_applied deve ser uma lista")

    return (len(errors) == 0 and is_valid, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    required_vars = [
        "LANGSMITH_ENDPOINT",
        "LANGSMITH_API_KEY",
        "USERNAME_LANGSMITH_HUB",
    ]

    if not check_env_vars(required_vars):
        return 1

    prompts = load_yaml(PROMPT_LOCAL_PATH)
    if not prompts:
        return 1

    prompt_data = prompts.get(PROMPT_KEY)
    if not prompt_data:
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPT_LOCAL_PATH}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/{PROMPT_KEY}"

    if push_prompt_to_langsmith(prompt_name, prompt_data):
        print("\nPróximos passos:")
        print("1. Verifique o prompt em https://smith.langchain.com/prompts")
        print("2. Execute a avaliação: python src/evaluate.py")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
