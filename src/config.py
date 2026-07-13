import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUTS_DIR = PROJECT_ROOT / "inputs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LOCAL_WORKING_DIR = PROJECT_ROOT / "local-working"
PDF_DIR = PROJECT_ROOT / "PDF"
RESEARCH_DIR = LOCAL_WORKING_DIR
CHARTS_DIR = OUTPUTS_DIR / "charts"
ANALYSIS_DIR = OUTPUTS_DIR / "analysis"

INGESTION_MODEL = "google/gemini-2.5-flash"
INGESTION_API_URL = "https://openrouter.ai/api/v1/chat/completions"
CORRECTION_MODEL = "deepseek-v4-flash"
SUMMARY_MODEL = "deepseek-v4-flash"

CORRECTION_TEMPERATURE = 0.6
SUMMARY_TEMPERATURE = 0.8
REQUEST_TIMEOUT = 120
INGESTION_TIMEOUT = 30
MAX_RETRIES = 3
MAX_WORKERS = 5
MAX_OUTPUT_TOKENS = 4096
MULTI_TOKEN_THRESHOLD = 3

MAX_LONG_SIDE = 1024
JPEG_QUALITY = 90
JITTER_MIN = 0.5
JITTER_MAX = 2.0

B1_TARGET = 12
B2_TARGET = 7
SHORT_TEXT_MSG = "Your writing was too short to give you error rate feedback. Please write at least 40 words to get a feedback score."


def get_api_key(name: str = "DEEPSEEK_API_KEY") -> str:
    key = os.environ.get(name)
    if not key:
        raise ValueError(f"{name} not set in environment")
    return key


ERRANT_CODE_NAMES = {
    "R:NOUN": "Problems with nouns",
    "R:NOUN:NUM": "Problems with singular and plural nouns",
    "R:NOUN:POSS": "Problems with possessive nouns",
    "R:NOUN:INFL": "Problems with noun inflection",
    "R:VERB": "Problems with verbs",
    "R:VERB:TENSE": "Problems with verb tense",
    "R:VERB:SVA": "Problems with subject-verb agreement",
    "R:VERB:FORM": "Problems with verb form (gerunds and infinitives)",
    "R:VERB:INFL": "Problems with verb inflection",
    "R:ADJ": "Problems with adjectives",
    "R:ADJ:FORM": "Problems with adjective form (comparatives and superlatives)",
    "R:ADV": "Problems with adverbs",
    "R:PREP": "Problems with prepositions",
    "R:PRON": "Problems with pronouns",
    "R:DET": "Problems with determiners (a, an, the)",
    "R:CONJ": "Problems with conjunctions",
    "R:PART": "Problems with particles",
    "R:PUNCT": "Problems with punctuation",
    "R:SPELL": "Spelling or capitalisation mistakes",
    "R:ORTH": "Capitalisation and spacing errors",
    "R:MORPH": "Problems with word formation (prefixes and suffixes)",
    "R:WO": "Problems with word order",
    "R:CONTR": "Problems with contractions",
    "M:NOUN": "Missing noun",
    "M:NOUN:NUM": "Missing plural noun ending",
    "M:VERB": "Missing verb",
    "M:VERB:TENSE": "Missing auxiliary verb",
    "M:VERB:FORM": "Missing verb form",
    "M:PREP": "Missing preposition",
    "M:PRON": "Missing pronoun",
    "M:DET": "Missing determiner (a, an, the)",
    "M:CONJ": "Missing conjunction",
    "M:PART": "Missing particle",
    "M:PUNCT": "Missing punctuation",
    "U:NOUN": "Unnecessary noun",
    "U:VERB": "Unnecessary verb",
    "U:PREP": "Unnecessary preposition",
    "U:PRON": "Unnecessary pronoun",
    "U:DET": "Unnecessary determiner",
    "U:CONJ": "Unnecessary conjunction",
    "U:PART": "Unnecessary particle",
    "U:PUNCT": "Unnecessary punctuation",
    "OTHER": "Other errors",
    "UNK": "Unidentified error type",
}

ERRANT_CODE_TO_COLUMN = {
    "R:NOUN": "r_noun", "R:NOUN:NUM": "r_noun_num", "R:NOUN:POSS": "r_noun_poss", "R:NOUN:INFL": "r_noun_infl",
    "R:VERB": "r_verb", "R:VERB:TENSE": "r_verb_tense", "R:VERB:SVA": "r_verb_sva",
    "R:VERB:FORM": "r_verb_form", "R:VERB:INFL": "r_verb_infl",
    "R:ADJ": "r_adj", "R:ADJ:FORM": "r_adj_form",
    "R:ADV": "r_adv", "R:PREP": "r_prep", "R:PRON": "r_pron", "R:DET": "r_det",
    "R:CONJ": "r_conj", "R:PART": "r_part", "R:PUNCT": "r_punct",
    "R:SPELL": "r_spell", "R:ORTH": "r_orth", "R:MORPH": "r_morph",
    "R:WO": "r_wo", "R:CONTR": "r_contr",
    "M:NOUN": "m_noun", "M:NOUN:NUM": "m_noun_num",
    "M:VERB": "m_verb", "M:VERB:TENSE": "m_verb_tense", "M:VERB:FORM": "m_verb_form",
    "M:PREP": "m_prep", "M:PRON": "m_pron", "M:DET": "m_det",
    "M:CONJ": "m_conj", "M:PART": "m_part", "M:PUNCT": "m_punct",
    "U:NOUN": "u_noun", "U:VERB": "u_verb", "U:PREP": "u_prep", "U:PRON": "u_pron",
    "U:DET": "u_det", "U:CONJ": "u_conj", "U:PART": "u_part", "U:PUNCT": "u_punct",
    "OTHER": "other", "UNK": "unk",
}

ERROR_CODE_COLUMNS = list(ERRANT_CODE_TO_COLUMN.values())
