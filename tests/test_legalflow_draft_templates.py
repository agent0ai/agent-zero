import pytest

from agent import Agent, AgentContext, UserMessage
from initialize import initialize_agent


@pytest.mark.asyncio
async def test_draft_template_peticao_inicial_contains_key_sections():
    config = initialize_agent(override_settings={"agent_profile": "legalflow_draft"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: draft\n"
                    "jurisdiction: SP, Brasil\n"
                    "document_type: petição inicial\n"
                    "facts: Resumo: conflito contratual.\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "# Rascunho — petição inicial" in result
        assert "## Partes" in result
        assert "## Dos Fatos" in result
        assert "## Do Direito" in result
        assert "## Dos Pedidos" in result
        assert "## Disclaimer" in result
        assert "não constitui aconselhamento jurídico" in result.lower()
        assert "{{" in result
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_draft_template_contestacao_contains_key_sections():
    config = initialize_agent(override_settings={"agent_profile": "legalflow_draft"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: draft\n"
                    "jurisdiction: SP, Brasil\n"
                    "document_type: contestação\n"
                    "facts: Resumo: defesa a ser apresentada.\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "# Rascunho — contestação" in result
        assert "## Partes" in result
        assert "## Dos Fatos" in result
        assert "## Do Direito" in result
        assert "## Dos Pedidos" in result
        assert "## Disclaimer" in result
        assert "{{" in result
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_draft_template_apelacao_contains_key_sections():
    config = initialize_agent(override_settings={"agent_profile": "legalflow_draft"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: draft\n"
                    "jurisdiction: SP, Brasil\n"
                    "document_type: apelação\n"
                    "facts: Resumo: sentença desfavorável.\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "# Rascunho — apelação" in result
        assert "## Partes" in result
        assert "## Tempestividade" in result
        assert "## Razões de Apelação" in result
        assert "## Dos Pedidos" in result
        assert "## Disclaimer" in result
        assert "{{" in result
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_draft_template_contrato_prestacao_servicos_contains_key_sections():
    config = initialize_agent(override_settings={"agent_profile": "legalflow_draft"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: draft\n"
                    "jurisdiction: SP, Brasil\n"
                    "document_type: contrato prestação de serviços\n"
                    "facts: Resumo: prestação de serviços de consultoria.\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "# Rascunho — contrato prestação de serviços" in result
        assert "## Objeto" in result
        assert "## Obrigações" in result
        assert "## Prazo" in result
        assert "## Remuneração" in result
        assert "## Rescisão" in result
        assert "## Foro" in result
        assert "## Disclaimer" in result
        assert "{{" in result
    finally:
        AgentContext.remove(agent.context.id)


@pytest.mark.asyncio
async def test_draft_rejects_unsupported_document_type():
    config = initialize_agent(override_settings={"agent_profile": "legalflow_draft"})
    agent = Agent(0, config)
    try:
        agent.hist_add_user_message(
            UserMessage(
                message=(
                    "intent: draft\n"
                    "jurisdiction: SP, Brasil\n"
                    "document_type: demand letter\n"
                    "facts: Resumo: cobrança.\n"
                ),
                attachments=[],
            )
        )
        result = await agent.monologue()
        assert "unsupported or missing `document_type`" in result
        assert "petição inicial" in result
        assert "contestação" in result
        assert "apelação" in result
        assert "contrato prestação de serviços" in result
    finally:
        AgentContext.remove(agent.context.id)
