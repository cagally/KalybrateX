# Tests for Code Extractor
"""Tests for evaluator/code_extractor.py"""

import pytest

from evaluator.code_extractor import (
    extract_code_blocks,
    extract_code,
    extract_python_code,
    normalize_language,
    detect_primary_language,
    CodeBlock,
)


class TestNormalizeLanguage:
    """Tests for language normalization."""

    def test_python_aliases(self):
        assert normalize_language("python") == "python"
        assert normalize_language("py") == "python"
        assert normalize_language("python3") == "python"
        assert normalize_language("Python") == "python"

    def test_javascript_aliases(self):
        assert normalize_language("javascript") == "javascript"
        assert normalize_language("js") == "javascript"

    def test_bash_aliases(self):
        assert normalize_language("bash") == "bash"
        assert normalize_language("sh") == "bash"
        assert normalize_language("shell") == "bash"

    def test_unknown_language(self):
        assert normalize_language("unknown") == "unknown"
        assert normalize_language("cobol") == "cobol"


class TestExtractCodeBlocks:
    """Tests for code block extraction."""

    def test_single_python_block(self):
        response = """Here's some code:

```python
def hello():
    print("Hello World")
```

That's all!"""

        blocks = extract_code_blocks(response)
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert "def hello():" in blocks[0].code

    def test_multiple_blocks(self):
        response = """First Python:

```python
x = 1
```

Then JavaScript:

```javascript
const y = 2;
```
"""

        blocks = extract_code_blocks(response)
        assert len(blocks) == 2
        assert blocks[0].language == "python"
        assert blocks[1].language == "javascript"

    def test_no_language_specified(self):
        response = """Some code:

```
plain text code
```
"""
        blocks = extract_code_blocks(response)
        assert len(blocks) == 1
        assert blocks[0].language == "text"

    def test_empty_response(self):
        blocks = extract_code_blocks("")
        assert len(blocks) == 0

    def test_no_code_blocks(self):
        response = "Just some text without any code blocks."
        blocks = extract_code_blocks(response)
        assert len(blocks) == 0


class TestDetectPrimaryLanguage:
    """Tests for primary language detection."""

    def test_single_language(self):
        blocks = [CodeBlock("python", "x = 1", 1, 2)]
        assert detect_primary_language(blocks) == "python"

    def test_prefers_executable(self):
        blocks = [
            CodeBlock("json", '{"a": 1}', 1, 2),
            CodeBlock("python", "x = 1", 3, 4),
            CodeBlock("json", '{"b": 2}', 5, 6),
        ]
        # Should prefer Python (executable) over JSON (data)
        assert detect_primary_language(blocks) == "python"

    def test_empty_blocks(self):
        assert detect_primary_language([]) == "text"

    def test_frequency_tiebreaker(self):
        blocks = [
            CodeBlock("python", "x = 1", 1, 2),
            CodeBlock("python", "y = 2", 3, 4),
            CodeBlock("bash", "ls", 5, 6),
        ]
        # Python appears more frequently
        assert detect_primary_language(blocks) == "python"


class TestExtractCode:
    """Tests for the main extract_code function."""

    def test_extracts_python(self):
        response = """Here's the solution:

```python
import os

def main():
    print("Hello")

if __name__ == "__main__":
    main()
```
"""
        result = extract_code(response)
        assert result.has_executable_code
        assert result.primary_language == "python"
        assert "import os" in result.combined_code
        assert len(result.blocks) == 1

    def test_combines_multiple_python_blocks(self):
        response = """First import:

```python
import json
```

Then the function:

```python
def process(data):
    return json.dumps(data)
```
"""
        result = extract_code(response)
        assert result.has_executable_code
        assert "import json" in result.combined_code
        assert "def process" in result.combined_code

    def test_no_executable_code(self):
        response = """Here's some JSON:

```json
{"key": "value"}
```
"""
        result = extract_code(response)
        assert not result.has_executable_code
        assert result.primary_language == "json"

    def test_mixed_languages(self):
        response = """Python code:

```python
print("hello")
```

And some YAML config:

```yaml
name: test
```
"""
        result = extract_code(response)
        # Should detect Python as primary and combine only Python
        assert result.primary_language == "python"
        assert "print" in result.combined_code
        assert "name:" not in result.combined_code


class TestExtractPythonCode:
    """Tests for Python-specific extraction."""

    def test_extracts_only_python(self):
        response = """Python:

```python
x = 1
```

JavaScript:

```javascript
const y = 2;
```
"""
        python_code = extract_python_code(response)
        assert python_code is not None
        assert "x = 1" in python_code
        assert "const y" not in python_code

    def test_returns_none_when_no_python(self):
        response = """Only JavaScript:

```javascript
const x = 1;
```
"""
        assert extract_python_code(response) is None
