"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml
DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import check_env_vars, print_section_header, save_yaml

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SEED_PROMPT_NAME = 'leonanluppi/bug_to_user_story_v1'
OUTPUT_PATH = ROOT / 'prompts' / 'bug_to_user_story_v1.yml'


def _template_text(message) -> str:
    """Extract the raw template string from a LangChain message prompt."""
    prompt_obj = getattr(message, 'prompt', None)
    if prompt_obj is not None and hasattr(prompt_obj, 'template'):
        template = prompt_obj.template
        if isinstance(template, str):
            return template

    template = getattr(message, 'template', None)
    if isinstance(template, str):
        return template

    return ''


def _message_role(message) -> str:
    """Map a message prompt class to system or user."""
    class_name = type(message).__name__.lower()
    if 'system' in class_name:
        return 'system'
    if 'human' in class_name or 'user' in class_name:
        return 'user'

    role = getattr(message, 'role', None)
    if role == 'system':
        return 'system'
    return 'user'


def _split_messages(prompt) -> tuple[str, str]:
    system_prompt = ''
    user_prompt = ''

    for message in getattr(prompt, 'messages', []):
        role = _message_role(message)
        text = _template_text(message)
        if role == 'system' and not system_prompt:
            system_prompt = text
        elif role == 'user' and not user_prompt:
            user_prompt = text

    return system_prompt, user_prompt


def pull_prompts_from_langsmith():
    """Pull the seed prompt and save it as local YAML."""
    print_section_header('PULL DE PROMPTS DO LANGSMITH')

    if not check_env_vars(['LANGSMITH_API_KEY']):
        return None

    print(f'Puxando prompt: {SEED_PROMPT_NAME}')
    client = Client()
    prompt = client.pull_prompt(
        SEED_PROMPT_NAME,
        dangerously_pull_public_prompt=True,
    )

    system_prompt, user_prompt = _split_messages(prompt)
    if not system_prompt and not user_prompt:
        print('❌ O prompt puxado não contém mensagens de system ou user.')
        return None

    if not system_prompt:
        print('⚠️  O prompt puxado não tem system prompt.')
    if not user_prompt:
        print('⚠️  O prompt puxado não tem user prompt.')

    data = {
        'bug_to_user_story_v1': {
            'description': 'Prompt para converter relatos de bugs em User Stories',
            'system_prompt': system_prompt,
            'user_prompt': user_prompt or '{bug_report}',
            'version': 'v1',
            'created_at': '2025-01-15',
            'tags': ['bug-analysis', 'user-story', 'product-management'],
        }
    }

    if not save_yaml(data, str(OUTPUT_PATH)):
        return None

    print(f'✓ Prompt salvo em {OUTPUT_PATH}')
    return data


def main():
    """Função principal"""
    try:
        result = pull_prompts_from_langsmith()
    except Exception as exc:
        print(f'❌ Falha ao puxar o prompt: {exc}')
        return 1

    return 0 if result else 1


if __name__ == '__main__':
    sys.exit(main())
