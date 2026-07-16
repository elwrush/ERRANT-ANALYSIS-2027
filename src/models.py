from pydantic import BaseModel, Field, field_validator


class IngestionOutput(BaseModel):
    student_id: str
    student_text: str
    word_count: int
    name: str = ""
    class_: str = Field(default="", alias="class")
    source_images: list[str] = []

    @field_validator("student_id")
    @classmethod
    def five_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError(f"student_id must be 5 digits, got '{v}'")
        return v

    @field_validator("student_text")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("student_text must not be empty")
        return v

    @field_validator("word_count")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"word_count must be >= 1, got {v}")
        return v


class Metadata(BaseModel):
    model: str = "deepseek-v4-flash"
    identity_check: bool = False
    overcorrection_count: int = 0
    overcorrection_warnings: list[dict] = []
    total_edit_count: int = 0
    edit_width_stats: dict = {}

    @field_validator("overcorrection_count")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"overcorrection_count must be >= 0, got {v}")
        return v

    @field_validator("total_edit_count")
    @classmethod
    def total_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"total_edit_count must be >= 0, got {v}")
        return v


class ErrantAnalysis(BaseModel):
    errors: list[dict] = []
    uncategorised: list[dict] = []
    dropped_edits: dict = {}


class ErrantOutput(BaseModel):
    student_id: str
    original_text: str
    corrected_text: str
    sentence_pairs: list[dict] = []
    corrected_typst: str = ""
    error_rate: int | None = None
    word_count: int = 0
    name: str = ""
    class_: str = Field(default="", alias="class")
    record_id: str | None = None
    submission_date: str = ""
    topic: str = ""
    summary: str = ""
    summary_data: dict | None = None
    summary_type: str = ""
    date_created: str = ""
    metadata: Metadata = Metadata()
    errant_analysis: ErrantAnalysis = ErrantAnalysis()

    @field_validator("student_id")
    @classmethod
    def five_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError(f"student_id must be 5 digits, got '{v}'")
        return v

    @field_validator("original_text")
    @classmethod
    def orig_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("original_text must not be empty")
        return v

    @field_validator("corrected_text")
    @classmethod
    def cor_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("corrected_text must not be empty")
        return v

    @field_validator("error_rate")
    @classmethod
    def range_check(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError(f"error_rate must be 0-100 or None, got {v}")
        return v


class ReportData(BaseModel):
    student_id: str
    name: str
    class_: str = Field(alias="class")
    word_count: int
    error_rate: int | None = None
    summary_praise: str = ""
    summary_rendered: str = ""
    corrected_markup: str = ""
    original_text: str = ""
    chart_path: str = ""
    target_rate: int = 7
    cefr_level: str = "B2"

    @field_validator("student_id")
    @classmethod
    def five_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError(f"student_id must be 5 digits, got '{v}'")
        return v
