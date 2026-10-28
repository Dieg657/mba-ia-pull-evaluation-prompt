"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from utils import check_env_vars, load_yaml, print_section_header, validate_prompt_structure

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / 'prompts' / 'bug_to_user_story_v2.yml'
PROMPT_NAME = 'bug_to_user_story_v2'


def _prompt_entry(data: dict) -> dict:
    """Return the inner prompt mapping whether or not the YAML wraps it."""
    if 'system_prompt' in data:
        return data

    for value in data.values():
        if isinstance(value, dict) and 'system_prompt' in value:
            return value

    return {}


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)
    errors = list(errors)

    user_prompt = str(prompt_data.get('user_prompt', ''))
    if '{bug_report}' not in user_prompt:
        errors.append('user_prompt precisa conter a variável {bug_report}')

    system_prompt = str(prompt_data.get('system_prompt', ''))
    if '{bug_report}' in system_prompt:
        errors.append('system_prompt não deve repetir {bug_report}; ele fica só no user prompt')

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv('USERNAME_LANGSMITH_HUB', '').strip()
    identifier = f'{username}/{prompt_name}'

    chat_prompt = ChatPromptTemplate.from_messages([
        ('system', prompt_data['system_prompt']),
        ('user', prompt_data['user_prompt']),
    ])

    tags = list(prompt_data.get('tags') or [])
    for technique in prompt_data.get('techniques_applied') or []:
        tag = f'technique:{technique}'
        if tag not in tags:
            tags.append(tag)

    description = prompt_data.get('description', '')
    version = str(prompt_data.get('version') or '').strip()
    if version:
        description = f'{version}. {description}'
        if version not in tags:
            tags.append(version)
    techniques = prompt_data.get('techniques_applied') or []
    if techniques:
        techniques_text = ', '.join(str(technique) for technique in techniques)
        description = f'{description} Técnicas: {techniques_text}.'

    print(f'Publicando {identifier} (público)...')
    client = Client()
    url = client.push_prompt(
        identifier,
        object=chat_prompt,
        is_public=True,
        description=description,
        tags=tags,
    )

    print(f'✓ Prompt publicado: {url}')
    return True


def main():
    """Função principal"""
    print_section_header('PUSH DE PROMPTS OTIMIZADOS')
    print(f'Arquivo local: {PROMPT_PATH}')

    if not check_env_vars(['LANGSMITH_API_KEY', 'USERNAME_LANGSMITH_HUB']):
        return 1

    data = load_yaml(str(PROMPT_PATH))
    if not data:
        return 1

    prompt_data = _prompt_entry(data)
    version = str(prompt_data.get('version', ''))
    print(f'Versão: {version}')
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print('❌ Prompt inválido:')
        for error in errors:
            print(f'   - {error}')
        return 1

    print('✓ Estrutura do prompt validada')

    try:
        pushed = push_prompt_to_langsmith(PROMPT_NAME, prompt_data)
    except Exception as exc:
        print(f'❌ Falha ao publicar o prompt: {exc}')
        return 1

    return 0 if pushed else 1


if __name__ == '__main__':
    sys.exit(main())
