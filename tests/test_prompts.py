"""
Testes automatizados para validação de prompts.
"""
import sys
from pathlib import Path
import pytest
import yaml
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from utils import validate_prompt_structure

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / 'prompts' / 'bug_to_user_story_v2.yml'


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _load_v2() -> dict:
    data = load_prompts(str(PROMPT_PATH))
    assert 'bug_to_user_story_v2' in data
    return data['bug_to_user_story_v2']


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = _load_v2()
        system_prompt = prompt.get('system_prompt', '')
        assert isinstance(system_prompt, str)
        assert system_prompt.strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = _load_v2()['system_prompt'].lower()
        assert 'você é um product manager' in system_prompt

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = _load_v2()['system_prompt'].lower()
        assert 'markdown' in system_prompt
        assert 'como um' in system_prompt
        assert 'critérios de aceitação' in system_prompt

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = _load_v2()['system_prompt'].lower()
        assert 'exemplo 1' in system_prompt
        assert 'exemplo 2' in system_prompt
        assert 'relato:' in system_prompt
        assert 'user story:' in system_prompt

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        raw = PROMPT_PATH.read_text(encoding='utf-8')
        assert '[TODO]' not in raw
        assert 'TODO' not in _load_v2()['system_prompt']

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt = _load_v2()
        techniques = prompt.get('techniques_applied') or []
        assert isinstance(techniques, list)
        assert len(techniques) >= 2

        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
