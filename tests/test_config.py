import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)


class TestConfigPaths:
    def test_config_imports(self):
        import config
        assert config.PROJECT_ROOT.exists()
        assert config.OUTPUTS_DIR.name == "outputs"
        assert config.LOCAL_WORKING_DIR.name == "local-working"

    def test_errant_code_mappings_complete(self):
        import config
        assert len(config.ERRANT_CODE_NAMES) > 0
        assert len(config.ERRANT_CODE_TO_COLUMN) > 0
        assert len(config.ERRANT_CODE_TO_COLUMN) == len(config.ERRANT_CODE_NAMES)
        assert len(config.ERROR_CODE_COLUMNS) == len(config.ERRANT_CODE_NAMES)
        # Every code in NAMES must have a column mapping
        for code in config.ERRANT_CODE_NAMES:
            assert code in config.ERRANT_CODE_TO_COLUMN, f"{code} missing from ERRANT_CODE_TO_COLUMN"

    def test_model_constants(self):
        import config
        assert config.CORRECTION_MODEL == "deepseek-v4-flash"
        assert config.INGESTION_MODEL == "google/gemini-2.5-flash"
        assert config.B1_TARGET == 15
        assert config.B2_TARGET == 10

    def test_get_api_key_raises_when_missing(self):
        import config
        import pytest
        key = "TEST_NONEXISTENT_KEY_XYZ"
        if key not in os.environ:
            with pytest.raises(ValueError, match=key):
                config.get_api_key(key)
