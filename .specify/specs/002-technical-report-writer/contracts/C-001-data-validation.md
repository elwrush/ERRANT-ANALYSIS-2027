# Contract C-001: Data Validation

## Function Signature

```python
def validate_input_files(data_path: Path) -> ValidationResult:
    """
    Validate all JSON files in data_path against ErrantOutput model.

    Args:
        data_path: Directory containing ERRANT analysis JSON files.

    Returns:
        ValidationResult with valid/invalid file lists and per-field error details.

    Raises:
        FileNotFoundError: If data_path does not exist.
        ValueError: If data_path contains no .json files.
    """
```

## Output Schema

```python
class ValidationResult(BaseModel):
    valid_files: list[Path]
    invalid_files: list[InvalidFile]
    total_checked: int

class InvalidFile(BaseModel):
    path: Path
    errors: list[ValidationError]

class ValidationError(BaseModel):
    field: str
    message: str
```

## Contract Tests

| Test | Input | Expected |
|------|-------|----------|
| Valid single file | Path with one valid ErrantOutput JSON | 1 valid, 0 invalid |
| Multiple valid files | Path with 3 valid JSONs | 3 valid, 0 invalid |
| Invalid field value | JSON with empty original_text | 0 valid, 1 invalid with "original_text must not be empty" |
| Missing required field | JSON without student_id | 0 valid, 1 invalid |
| Non-JSON file | Path containing a .txt file | 0 valid, 0 invalid (skipped) |
| Empty directory | Empty directory | ValueError raised |
| Non-existent path | Path('does/not/exist') | FileNotFoundError raised |
