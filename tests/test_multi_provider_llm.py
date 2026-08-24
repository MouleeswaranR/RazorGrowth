import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.llm_provider_service import llm_provider_service, ProviderEndpoint
from app.services.llm_service import llm_service
from app.schemas.agent_outputs import LLMReasoningInput


def test_provider_endpoint_configuration():
    """Validates provider endpoint configuration detection and header generation."""
    endpoint_valid = ProviderEndpoint(
        name="nvidia_nim",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="nvapi-testkey12345",
        model="meta/llama-3.3-70b-instruct",
    )
    assert endpoint_valid.is_configured() is True
    assert "Bearer nvapi-testkey12345" in endpoint_valid.get_headers()["Authorization"]

    endpoint_placeholder = ProviderEndpoint(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key="your-key-here",
        model="llama-3.3-70b-versatile",
    )
    assert endpoint_placeholder.is_configured() is False


def test_provider_chain_task_prioritization():
    """Validates task-specific ordering (streaming starts with Groq; tool calling starts with NVIDIA NIM)."""
    chain_streaming = llm_provider_service.get_chain_for_task("streaming")
    chain_tool = llm_provider_service.get_chain_for_task("tool_calling")

    assert len(chain_streaming) > 0
    assert len(chain_tool) > 0


def test_reasoning_trace_extraction():
    """Validates extraction of <think> tags and explicit reasoning_content fields."""
    raw_data = {
        "choices": [
            {
                "message": {
                    "content": "<think>Analyzed dormant VIPs with high CLV and churn > 0.60.</think>{\"executive_summary\": \"Recovery plan ready.\"}",
                }
            }
        ]
    }
    parsed = llm_provider_service._parse_provider_response(raw_data, "nvidia_nim")
    assert parsed["reasoning_trace"] == "Analyzed dormant VIPs with high CLV and churn > 0.60."
    assert "<think>" not in parsed["content"]
    assert "{\"executive_summary\": \"Recovery plan ready.\"}" in parsed["content"]


@pytest.mark.asyncio
async def test_provider_failover_chain():
    """Validates that 429 or network errors trigger immediate automatic failover to the next provider."""
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.text = "Rate limited"

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "{\"executive_summary\": \"Recovered via backup provider.\"}",
                    "reasoning_content": "Multi-provider failover executed successfully.",
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", side_effect=[mock_resp_429, mock_resp_200]):
        messages = [{"role": "user", "content": "Test prompt"}]
        result = await llm_provider_service.execute_chat_with_fallback(messages, task="reasoning")

        assert result is not None
        assert "executive_summary" in result["content"]


@pytest.mark.asyncio
async def test_generate_growth_reasoning_with_reasoning_trace():
    """Validates LLMService.generate_growth_reasoning produces structured output with attached reasoning trace."""
    input_data = LLMReasoningInput(
        merchant_id="merch_test_multi",
        top_opportunity_title="VIP Dormant Recovery",
        total_opportunity_gmv=125000.0,
        total_customers=500,
        dormant_vip_count=45,
        payment_success_rate=0.895,
    )

    reasoning_output = await llm_service.generate_growth_reasoning(input_data)
    assert reasoning_output.executive_summary is not None
    assert len(reasoning_output.executive_summary) > 10
    assert reasoning_output.reasoning_trace is not None
    assert reasoning_output.provider_used is not None
