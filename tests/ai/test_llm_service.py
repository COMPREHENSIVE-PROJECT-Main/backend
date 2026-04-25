import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.ai.models.state import AgentMessage, AgentRole
from app.ai.schemas.llm_schema import AgentStructuredOutput
from app.ai.services import llm_service


class LLMServiceTest(unittest.TestCase):
    def test_call_llm_uses_azure_json_mode(self):
        create = Mock(
            return_value=SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        finish_reason="stop",
                        message=SimpleNamespace(content='{"summary":"ok"}'),
                    )
                ]
            )
        )
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=create)
            )
        )

        with patch("app.ai.services.llm_service._get_azure_client", return_value=fake_client):
            output = llm_service.call_llm("system", "user JSON", json_mode=True)

        self.assertEqual(output, '{"summary":"ok"}')
        self.assertEqual(
            create.call_args.kwargs["response_format"],
            {"type": "json_object"},
        )

    def test_extract_json_object_from_code_fence(self):
        payload = llm_service._extract_json_object('```json\n{"summary": "ok"}\n```')

        self.assertEqual(payload, {"summary": "ok"})

    def test_call_llm_json_validates_schema(self):
        raw = (
            '{"summary": "요약", "key_points": ["쟁점"], '
            '"cited_rules": ["민법 제750조"], "content": "본문"}'
        )

        with patch("app.ai.services.llm_service.call_llm", return_value=raw):
            output = llm_service.call_llm_json("system", "user", AgentStructuredOutput, retries=0)

        self.assertEqual(output.summary, "요약")
        self.assertEqual(output.key_points, ["쟁점"])
        self.assertEqual(output.cited_rules, ["민법 제750조"])
        self.assertEqual(output.content, "본문")

    def test_json_output_instruction_uses_template_not_schema(self):
        instruction = llm_service._json_output_instruction(AgentStructuredOutput)

        self.assertIn('"summary"', instruction)
        self.assertIn('"content"', instruction)
        self.assertNotIn('"properties"', instruction)
        self.assertNotIn('"required"', instruction)

    def test_format_debate_history_truncates_long_text(self):
        messages = [
            AgentMessage(
                role=AgentRole.PROSECUTOR,
                agent_name="검사",
                round_number=0,
                position="변론",
                summary="요약",
                content="가" * 100,
            )
        ]

        rendered = llm_service.format_debate_history(messages, max_chars=20)

        self.assertTrue(rendered.startswith("[이전 발언 일부 생략]"))
        self.assertLessEqual(len(rendered), len("[이전 발언 일부 생략]\n") + 20)


if __name__ == "__main__":
    unittest.main()
