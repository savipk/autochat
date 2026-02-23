"""
Tests for core framework components.
All imports done inside test methods to avoid langchain_openai/numpy segfault at collection time.
"""

import asyncio
import os
import pytest


class TestAgentConfig:
    def test_config_creation(self):
        from core.agent.config import AgentConfig
        config = AgentConfig(
            name="test",
            description="A test agent",
            llm=None,
            tools=[],
            system_prompt="You are a test agent.",
        )
        assert config.name == "test"
        assert config.description == "A test agent"
        assert config.tools == []

    def test_config_defaults(self):
        from core.agent.config import AgentConfig
        config = AgentConfig(name="test", description="test", llm=None)
        assert config.middleware == []
        assert config.state_schema is None
        assert config.context_schema is None
        assert config.context_factory is None

    def test_config_context_factory(self):
        from core.agent.config import AgentConfig
        from core.state import BaseContext
        factory = lambda tid: BaseContext(thread_id=tid)
        config = AgentConfig(name="test", description="test", llm=None, context_factory=factory)
        ctx = config.context_factory("abc")
        assert ctx.thread_id == "abc"


class TestAgentRegistry:
    def test_register_and_get(self):
        from core.agent.registry import AgentRegistry
        registry = AgentRegistry()

        class MockAgent:
            class config:
                name = "test_agent"

        agent = MockAgent()
        registry._agents["test_agent"] = agent
        assert registry.get("test_agent") is agent
        assert "test_agent" in registry

    def test_list_agents(self):
        from core.agent.registry import AgentRegistry
        registry = AgentRegistry()
        registry._agents["a"] = "agent_a"
        registry._agents["b"] = "agent_b"
        assert sorted(registry.list_agents()) == ["a", "b"]

    def test_get_missing(self):
        from core.agent.registry import AgentRegistry
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None


class TestAgentProtocol:
    def test_agent_card(self):
        from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill
        card = AgentCard(
            name="test",
            description="Test agent",
            skills=[AgentSkill(name="skill1", description="A skill")],
        )
        protocol = AgentProtocol(card)
        card_dict = protocol.get_agent_card()
        assert card_dict["name"] == "test"
        assert len(card_dict["skills"]) == 1
        assert card_dict["skills"][0]["name"] == "skill1"

    def test_task_lifecycle(self):
        from core.agent.protocol import Task, TaskState
        task = Task()
        assert task.state == TaskState.SUBMITTED
        task.state = TaskState.WORKING
        assert task.state == TaskState.WORKING

    def test_cancel_task(self):
        from core.agent.protocol import AgentProtocol, AgentCard, Task, TaskState
        card = AgentCard(name="test", description="test")
        protocol = AgentProtocol(card)
        task = Task()
        protocol._tasks[task.id] = task
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(protocol.cancel_task(task.id))
        loop.close()
        assert result is True
        assert task.state == TaskState.FAILED

    def test_cancel_missing_task(self):
        from core.agent.protocol import AgentProtocol, AgentCard
        card = AgentCard(name="test", description="test")
        protocol = AgentProtocol(card)
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(protocol.cancel_task("nonexistent"))
        loop.close()
        assert result is False


class TestSkillRegistry:
    def test_register_and_get(self):
        from core.skills.base import Skill, SkillRegistry
        registry = SkillRegistry()
        skill = Skill(name="test_skill", description="A test skill", path="/tmp/test.md")
        registry.register(skill)
        assert registry.get("test_skill") is skill
        assert "test_skill" in registry

    def test_list_skills(self):
        from core.skills.base import Skill, SkillRegistry
        registry = SkillRegistry()
        registry.register(Skill(name="s1", description="Skill 1"))
        registry.register(Skill(name="s2", description="Skill 2"))
        skills = registry.list_skills()
        assert len(skills) == 2
        names = [s["name"] for s in skills]
        assert "s1" in names
        assert "s2" in names

    def test_get_missing(self):
        from core.skills.base import SkillRegistry
        registry = SkillRegistry()
        assert registry.get("nonexistent") is None


class TestBaseContext:
    def test_defaults(self):
        from core.state import BaseContext
        ctx = BaseContext()
        assert ctx.thread_id == ""

    def test_custom_values(self):
        from core.state import BaseContext
        ctx = BaseContext(thread_id="t-123")
        assert ctx.thread_id == "t-123"

    def test_app_context_defaults(self):
        from core.state import AppContext
        ctx = AppContext()
        assert ctx.thread_id == ""
        assert ctx.first_name == ""
        assert ctx.display_name == ""

    def test_app_context_inherits_base(self):
        from core.state import BaseContext, AppContext
        assert issubclass(AppContext, BaseContext)

    def test_app_context_fields(self):
        from core.state import AppContext
        ctx = AppContext(thread_id="s-1", first_name="Alice", display_name="Alice Smith")
        assert ctx.thread_id == "s-1"
        assert ctx.first_name == "Alice"
        assert ctx.display_name == "Alice Smith"

    def test_mycareer_inherits(self):
        from core.state import BaseContext
        from agents.mycareer.agent import MyCareerContext
        assert issubclass(MyCareerContext, BaseContext)
        ctx = MyCareerContext(thread_id="t-1", completion_score=72)
        assert ctx.thread_id == "t-1"
        assert ctx.completion_score == 72

    def test_jd_generator_inherits(self):
        from core.state import BaseContext
        from agents.jd_generator.agent import JDGeneratorContext
        assert issubclass(JDGeneratorContext, BaseContext)
        ctx = JDGeneratorContext(thread_id="t-2")
        assert ctx.thread_id == "t-2"


class TestSkillContent:
    def test_load_content_from_file(self, tmp_path):
        from core.skills.base import Skill
        test_file = tmp_path / "test_skill.md"
        test_file.write_text("# Test Skill\nContent here.")
        skill = Skill(name="test", description="test", path=str(test_file))
        content = skill.load_content()
        assert "# Test Skill" in content
        assert "Content here." in content

    def test_load_jd_standards(self):
        from core.skills.base import Skill
        path = os.path.join(os.path.dirname(__file__), "..", "agents", "jd_generator", "skills", "jd_standards.md")
        skill = Skill(name="jd_standards", description="test", path=path)
        content = skill.load_content()
        assert "Corporate Job Description Standards" in content
        assert "Summary" in content
        assert "Responsibilities" in content
        assert "Qualifications" in content

    def test_load_missing_file(self):
        from core.skills.base import Skill
        skill = Skill(name="test", description="test", path="/nonexistent/path.md")
        content = skill.load_content()
        assert "not found" in content
