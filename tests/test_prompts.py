"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_optimized_prompt():
    """Carrega o prompt otimizado usado nas validações."""
    prompts = load_prompts(str(PROMPT_FILE))
    return prompts[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = load_optimized_prompt()
        is_valid, errors = validate_prompt_structure(prompt)

        assert is_valid, errors
        assert "system_prompt" in prompt
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = load_optimized_prompt()["system_prompt"]

        role_terms = [
            "Você é um Product Manager",
            "Product Manager sênior",
            "persona",
        ]

        assert any(term in system_prompt for term in role_terms)

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = load_optimized_prompt()["system_prompt"]

        assert "User Story" in system_prompt
        assert "Como [persona], eu quero [necessidade], para que [benefício]." in system_prompt
        assert "Critérios de Aceitação" in system_prompt

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt = load_optimized_prompt()
        system_prompt = prompt["system_prompt"]
        techniques = prompt.get("techniques_applied", [])

        assert "Few-shot Learning" in techniques
        assert system_prompt.count("Entrada:") >= 2
        assert system_prompt.count("Saída:") >= 2

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt = load_optimized_prompt()
        serialized_prompt = yaml.safe_dump(prompt, allow_unicode=True)

        assert "TODO" not in serialized_prompt
        assert "[TODO]" not in serialized_prompt

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = load_optimized_prompt().get("techniques_applied", [])

        assert isinstance(techniques, list)
        assert len(techniques) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])