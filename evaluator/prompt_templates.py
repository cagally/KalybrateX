# Prompt Templates for Execution Verification
"""
Templates for generating execution prompts that produce verifiable outputs.

Prompt Tiers:
- Tier 1 (Synthetic): Self-contained tasks with exact verification
- Tier 2 (Transform): Embedded data with deterministic outputs

Key principles:
- NO explicit "install dependencies" instructions (tests if skill teaches this)
- Self-contained (no external test files needed)
- Clear expected output for verification
"""

from dataclasses import dataclass
from typing import Optional

from evaluator.skill_categories import SkillCategory, get_skill_category


@dataclass
class ExecutionPrompt:
    """A prompt designed to produce executable, verifiable output."""
    prompt: str
    tier: int  # 1 or 2
    expected_files: list[str]
    expected_properties: dict  # filename -> expected properties
    capability_tested: str


# =============================================================================
# Tier 1: Synthetic Tasks (self-contained, exact verification)
# =============================================================================

TIER_1_PDF_PROMPTS = [
    ExecutionPrompt(
        prompt="Create a PDF file named 'test.pdf' with exactly 2 pages. Page 1 should contain the text 'Hello World'. Page 2 should contain the text 'Page Two'.",
        tier=1,
        expected_files=["test.pdf"],
        expected_properties={"test.pdf": {"pages": 2, "text_contains": ["Hello World", "Page Two"]}},
        capability_tested="basic_pdf_creation",
    ),
    ExecutionPrompt(
        prompt="Create a single-page PDF named 'simple.pdf' containing the text 'This is a test document' centered on the page.",
        tier=1,
        expected_files=["simple.pdf"],
        expected_properties={"simple.pdf": {"pages": 1, "text_contains": ["This is a test document"]}},
        capability_tested="single_page_pdf",
    ),
    ExecutionPrompt(
        prompt="Create a PDF named 'report.pdf' with 3 pages. Each page should display its page number: 'Page 1', 'Page 2', 'Page 3'.",
        tier=1,
        expected_files=["report.pdf"],
        expected_properties={"report.pdf": {"pages": 3}},
        capability_tested="multi_page_pdf",
    ),
    ExecutionPrompt(
        prompt="Generate a PDF file called 'invoice.pdf' with a header 'INVOICE' and a table with columns: Item, Quantity, Price. Add one row: Widget, 5, $10.00.",
        tier=1,
        expected_files=["invoice.pdf"],
        expected_properties={"invoice.pdf": {"pages": 1, "text_contains": ["INVOICE", "Widget"]}},
        capability_tested="pdf_with_table",
    ),
]

TIER_1_XLSX_PROMPTS = [
    ExecutionPrompt(
        prompt="Create an Excel file named 'data.xlsx' with a sheet called 'Sales'. Add headers in row 1: Date, Amount, Product. Add one data row: 2024-01-15, 100.00, Widget.",
        tier=1,
        expected_files=["data.xlsx"],
        expected_properties={"data.xlsx": {"sheet": "Sales"}},
        capability_tested="basic_xlsx_creation",
    ),
    ExecutionPrompt(
        prompt="Create an Excel file 'report.xlsx' with two sheets: 'Summary' and 'Details'. The Summary sheet should have a cell A1 with text 'Total: 500'.",
        tier=1,
        expected_files=["report.xlsx"],
        expected_properties={"report.xlsx": {"sheet": "Summary"}},
        capability_tested="multi_sheet_xlsx",
    ),
]

TIER_1_CODE_PROMPTS = [
    ExecutionPrompt(
        prompt="Write a Python script and save it to 'calculator.py' that defines a function 'add(a, b)' which returns the sum of two numbers. Include a test that prints add(2, 3).",
        tier=1,
        expected_files=["calculator.py"],
        expected_properties={"calculator.py": {}},
        capability_tested="basic_python_script",
    ),
    ExecutionPrompt(
        prompt="Create a Python file 'utils.py' with a function 'is_prime(n)' that returns True if n is prime, False otherwise. Include tests for is_prime(7) and is_prime(10).",
        tier=1,
        expected_files=["utils.py"],
        expected_properties={"utils.py": {}},
        capability_tested="algorithm_implementation",
    ),
]

TIER_1_CONFIG_PROMPTS = [
    ExecutionPrompt(
        prompt="Create a YAML configuration file named 'config.yaml' with the following structure: database.host='localhost', database.port=5432, debug=true.",
        tier=1,
        expected_files=["config.yaml"],
        expected_properties={"config.yaml": {"keys": ["database"]}},
        capability_tested="yaml_config_creation",
    ),
    ExecutionPrompt(
        prompt="Create a JSON file 'settings.json' with keys: name (string 'MyApp'), version (string '1.0.0'), features (array with 'auth' and 'api').",
        tier=1,
        expected_files=["settings.json"],
        expected_properties={"settings.json": {"keys": ["name", "version", "features"]}},
        capability_tested="json_config_creation",
    ),
]


# =============================================================================
# Tier 2: Transform Tasks (embedded data, deterministic output)
# =============================================================================

TIER_2_PDF_PROMPTS = [
    ExecutionPrompt(
        prompt="""Convert the following text into a PDF named 'output.pdf':

Title: Meeting Notes
Date: January 15, 2024
Attendees: Alice, Bob, Charlie

Discussion Points:
1. Project timeline review
2. Budget allocation
3. Next steps

Make sure all the text appears in the PDF.""",
        tier=2,
        expected_files=["output.pdf"],
        expected_properties={"output.pdf": {"pages": 1, "text_contains": ["Meeting Notes", "Alice"]}},
        capability_tested="text_to_pdf_conversion",
    ),
]

TIER_2_TRANSFORM_PROMPTS = [
    ExecutionPrompt(
        prompt="""Convert this JSON data to a YAML file named 'output.yaml':

{"name": "Alice", "age": 30, "city": "New York", "skills": ["Python", "SQL"]}

The YAML should preserve all the data.""",
        tier=2,
        expected_files=["output.yaml"],
        expected_properties={"output.yaml": {"keys": ["name", "age", "city", "skills"]}},
        capability_tested="json_to_yaml_conversion",
    ),
    ExecutionPrompt(
        prompt="""Convert this CSV data to JSON and save as 'output.json':

name,age,department
Alice,30,Engineering
Bob,25,Marketing
Charlie,35,Sales

Output should be an array of objects.""",
        tier=2,
        expected_files=["output.json"],
        expected_properties={"output.json": {}},
        capability_tested="csv_to_json_conversion",
    ),
]

TIER_2_CODE_PROMPTS = [
    ExecutionPrompt(
        prompt="""Create a Python script 'process.py' that:
1. Reads this data: [{"id": 1, "value": 10}, {"id": 2, "value": 20}, {"id": 3, "value": 30}]
2. Calculates the sum of all 'value' fields
3. Saves the result to 'result.json' as {"total": <sum>}

Execute the script to create result.json.""",
        tier=2,
        expected_files=["process.py", "result.json"],
        expected_properties={"result.json": {"keys": ["total"]}},
        capability_tested="data_processing_script",
    ),
]


# =============================================================================
# Prompt Selection
# =============================================================================

def get_execution_prompts(skill_name: str, count: int = 8) -> list[ExecutionPrompt]:
    """
    Get execution prompts appropriate for a skill.

    Args:
        skill_name: Name of the skill
        count: Number of prompts to return (split between Tier 1 and Tier 2)

    Returns:
        List of ExecutionPrompt objects
    """
    category = get_skill_category(skill_name)

    # Select prompts based on category
    if category == SkillCategory.FILE_ARTIFACT:
        if "pdf" in skill_name.lower():
            tier1 = TIER_1_PDF_PROMPTS
            tier2 = TIER_2_PDF_PROMPTS
        elif "xlsx" in skill_name.lower() or "excel" in skill_name.lower():
            tier1 = TIER_1_XLSX_PROMPTS
            tier2 = TIER_2_TRANSFORM_PROMPTS
        else:
            tier1 = TIER_1_PDF_PROMPTS  # Default to PDF
            tier2 = TIER_2_PDF_PROMPTS

    elif category == SkillCategory.CODE_GENERATION:
        tier1 = TIER_1_CODE_PROMPTS
        tier2 = TIER_2_CODE_PROMPTS

    elif category == SkillCategory.CONFIGURATION:
        tier1 = TIER_1_CONFIG_PROMPTS
        tier2 = TIER_2_TRANSFORM_PROMPTS

    else:
        # Advisory skills - no execution prompts
        return []

    # Split between tiers (roughly 50/50)
    tier1_count = count // 2
    tier2_count = count - tier1_count

    prompts = []
    prompts.extend(tier1[:tier1_count])
    prompts.extend(tier2[:tier2_count])

    return prompts


def get_prompt_generation_instruction(skill_name: str) -> str:
    """
    Get instruction for Sonnet to generate execution prompts.

    This is used when we want to dynamically generate prompts
    instead of using the pre-defined templates.

    Args:
        skill_name: Name of the skill

    Returns:
        Instruction string for prompt generation
    """
    category = get_skill_category(skill_name)

    base_instruction = """Generate execution prompts for testing the '{skill_name}' skill.

CRITICAL RULES:
1. DO NOT include phrases like "install dependencies" or "use pip install"
2. Tasks must be SELF-CONTAINED - no references to external files
3. Tasks should produce CONCRETE OUTPUT FILES that can be verified
4. Include the expected output filename in the prompt
5. Make prompts realistic - something a user would actually ask

"""

    if category == SkillCategory.FILE_ARTIFACT:
        return base_instruction + """
For this FILE ARTIFACT skill, generate prompts that:
- Ask to CREATE files (PDF, Excel, etc.) from scratch
- Specify exact content that should appear in the file
- Name the output file explicitly (e.g., 'output.pdf')

Example: "Create a PDF named 'report.pdf' with 3 pages containing..."
"""

    elif category == SkillCategory.CODE_GENERATION:
        return base_instruction + """
For this CODE GENERATION skill, generate prompts that:
- Ask for complete, runnable scripts
- Specify the output filename (e.g., 'script.py')
- Include clear requirements that can be tested

Example: "Create a Python script 'utils.py' that implements..."
"""

    elif category == SkillCategory.CONFIGURATION:
        return base_instruction + """
For this CONFIGURATION skill, generate prompts that:
- Ask for complete config files
- Specify the format (YAML, JSON, etc.)
- Include specific keys/values that should be present

Example: "Create a YAML config 'settings.yaml' with database connection..."
"""

    return base_instruction
