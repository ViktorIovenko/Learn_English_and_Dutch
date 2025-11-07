# bot/validators.py
# [ДОБАВЛЕНО v14] Вынесены парсинг CSV, нормализации и валидации примеров.

import csv
import re
from typing import Dict, List, Tuple

# ---------------- НАСТРОЙКИ ПРОВЕРОК ----------------
REQUIRE_EN_IN_EXAMPLE = True
CHECK_NL_IN_EXAMPLE = True
CHECK_RU_IN_EXAMPLE = True

# ---------------- МАППИНГ ЗАГОЛОВКОВ ----------------
HEADER_MAP = {
    "number": {"№", "no", "number", "номер", "num", "n", "id", "номерслова", "порядковыйномер", "ord", "ordernumber"},
    "lesson": {"урок", "lesson", "lessonname", "названиеурока", "урокимя"},
    "nl": {"нидерландское", "нидерландскоесл", "нидерландскоеслово", "dutch", "nl", "woordnl", "nederlands", "nederlandse"},
    "en": {"english", "английский", "en", "engels"},
    "ru": {"русский", "russian", "ru"},
    "ex_nl": {"пример(nl)", "примерnl", "example(nl)", "ex_nl", "voorbeeld", "voorbeeld(nl)", "примерпо-голландски"},
    "ex_en": {"пример(en)", "примерen", "example(en)", "ex_en", "примерпо-английски"},
    "ex_ru": {"пример(ru)", "примерru", "example(ru)", "ex_ru", "примерпо-русски"},
    "audio_nl": {"audionl", "audio nl", "аудиоnl", "аудио nl", "audio_nl"},
    "audio_en": {"audioen", "audio en", "аудиoen", "аудио en", "audio_en"},
    "audio_ru": {"audioru", "audio ru", "аудиoru", "аудио ru", "audio_ru"},
}
REQUIRED_KEYS_MIN = {"number", "nl", "en", "ru"}

# ---------------- ОБЩИЕ ХЕЛПЕРЫ ----------------
_CLEAN_RE = re.compile(r"[\s\.\,\-\_\(\)\[\]\{\}:;!?\u00A0]+", re.UNICODE)
_COMBINED_NUM_LESSON_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)*)\s*(.*)$")

def _clean_key(s: str) -> str:
    return _CLEAN_RE.sub("", (s or "").strip().lower())

def normalize_header(h: str) -> str:
    key = _clean_key(h)
    for norm, variants in HEADER_MAP.items():
        if key in variants or key == norm:
            return norm
    if key.startswith("пример") and "nl" in key:
        return "ex_nl"
    if key.startswith("пример") and "en" in key:
        return "ex_en"
    if key.startswith("пример") and ("ru" in key or "рус" in key):
        return "ex_ru"
    return key

def split_number_and_lesson(number_cell: str) -> Tuple[str, str]:
    text = (number_cell or "").strip()
    m = _COMBINED_NUM_LESSON_RE.match(text)
    if not m:
        return text, ""
    num = (m.group(1) or "").strip()
    rest = (m.group(2) or "").strip()
    return num, rest

def _seen_headers_str(headers: List[str]) -> str:
    return ", ".join(headers)

# ---------------- РАЗБОР ВАРИАНТОВ ----------------
NL_ARTICLES = {"de", "het", "een"}

# [ДОБАВЛЕНО v14] расширенный разбор вариантов: скобки → варианты; делим по / , ;
def extract_variants(value: str) -> List[str]:
    raw = (value or "").strip()
    variants: List[str] = []
    if not raw:
        return variants

    # внутри скобок как отдельные варианты
    in_paren = re.findall(r"\(([^)]*)\)", raw)
    for chunk in in_paren:
        for part in re.split(r"[\/,;]", chunk):
            p = part.strip()
            if p:
                variants.append(p)

    # строка без скобок
    no_paren = re.sub(r"\([^)]*\)", "", raw)
    for part in re.split(r"[\/,;]", no_paren):
        p = part.strip()
        if p:
            variants.append(p)

    # uniq, сохраняя порядок
    seen = set()
    uniq: List[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq

def normalize_nl_token(token: str) -> str:
    token = token.strip()
    pieces = [p for p in token.split() if p]
    pieces = [p for p in pieces if p.lower() not in NL_ARTICLES]
    return " ".join(pieces) if pieces else token

# ---------------- ПОИСК В ПРЕДЛОЖЕНИИ ----------------
def word_in_sentence_exact(word: str, sentence: str) -> bool:
    """Точное слово/фраза по границам (\w), регистронезависимо."""
    w = (word or "").strip()
    s = (sentence or "").strip()
    if not w or not s:
        return False
    pattern = r"(?<!\w)" + re.escape(w) + r"(?!\w)"
    return re.search(pattern, s, flags=re.IGNORECASE) is not None

# ----- Русская гибкая проверка (склонения) -----
def _norm_cyrillic(s: str) -> str:
    return (s or "").strip().lower().replace("ё", "е")

_RU_ENDINGS = [
    "иями","ями","ациям","ациях","ациями",
    "иями","ями","ами",
    "ов","ев","ёв","ей","ий",
    "ою","ею","ую","юю",
    "ью","ия","иям","иях","иями",
    "ами","ями","ях","ах",
    "ому","ему","ого","его","ими","ыми",
    "ой","ей","ою","ею","ых","их",
    "ам","ям","ом","ем","ах","ях",
    "ую","юю","ые","ие","ая","яя",
    "у","ю","а","я","е","и","ы","о",
]

def _ru_stem(word: str) -> str:
    w = _norm_cyrillic(word)
    w = re.sub(r"[^а-я]", "", w)
    if len(w) <= 3:
        return w
    for suf in _RU_ENDINGS:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w

def word_in_sentence_ru_flex_single(word: str, sentence: str) -> bool:
    """RU: одна лексема — «основа + любые буквы/дефис»."""
    base = _ru_stem(word)
    s = _norm_cyrillic(sentence)
    if not base or not s:
        return False
    pattern = r"(?<![а-я])" + re.escape(base) + r"[а-я\-]*"
    return re.search(pattern, s, flags=re.IGNORECASE) is not None

# [ДОБАВЛЕНО v14] RU вариант из нескольких слов: требуем присутствия КАЖДОГО слова варианта
def ru_variant_in_sentence(variant: str, sentence: str) -> bool:
    """
    «двоюродная сестра» → требуется, чтобы и «двоюродн-» и «сестр-» (по основе) нашлись в предложении.
    Порядок не важен.
    """
    tokens = [t for t in re.split(r"\s+", (variant or "").strip()) if t]
    if not tokens:
        return False
    return all(word_in_sentence_ru_flex_single(tok, sentence) for tok in tokens)

# ---------------- ОЖИДАЕМОЕ СЛОВО ДЛЯ СООБЩЕНИЙ ----------------
def expected_word_for(field_key: str, row: Dict[str, str]) -> str:
    if field_key == "ex_nl":
        variants = [normalize_nl_token(v) for v in extract_variants(row["nl"])]
        return " | ".join(variants[:3]) + (" ..." if len(variants) > 3 else "")
    if field_key == "ex_en":
        variants = extract_variants(row["en"])
        return " | ".join(variants[:3]) + (" ..." if len(variants) > 3 else "")
    if field_key == "ex_ru":
        variants = extract_variants(row["ru"])
        return " | ".join(variants[:3]) + (" ..." if len(variants) > 3 else "")
    return ""

# ---------------- ВАЛИДАЦИЯ ----------------
def validate_example_usage(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Делит строки на валидные и проблемные.
    Проблемные — где НИ ОДИН вариант слова не встречается в своём примере.
    Возвращает (valid_rows, bad_rows_with_reasons)
    bad_rows: {number, lesson, nl, en, ru, missing: list[str] ('ex_en','ex_nl','ex_ru')}
    """
    valid: List[Dict[str, str]] = []
    bad: List[Dict[str, str]] = []

    for r in rows:
        missing_fields: List[str] = []

        # EN — обязателен: достаточно ЛЮБОГО варианта
        if REQUIRE_EN_IN_EXAMPLE:
            en_variants = extract_variants(r["en"])
            if en_variants and not any(word_in_sentence_exact(v, r.get("ex_en", "")) for v in en_variants):
                missing_fields.append("ex_en")

        # NL — если есть пример: достаточно любого токена любого варианта (без артиклей)
        if CHECK_NL_IN_EXAMPLE and r.get("ex_nl"):
            nl_variants = [normalize_nl_token(v) for v in extract_variants(r["nl"])]
            tokens: List[str] = []
            for v in nl_variants:
                tokens.extend([p for p in v.split() if p])
            tokens = [t for t in tokens if t.lower() not in NL_ARTICLES]
            if not tokens:  # fallback
                tokens = nl_variants
            if not any(word_in_sentence_exact(tok, r["ex_nl"]) for tok in tokens):
                missing_fields.append("ex_nl")

        # RU — если есть пример: достаточно ЛЮБОГО варианта; для многословных вариант → все слова должны встретиться
        if CHECK_RU_IN_EXAMPLE and r.get("ex_ru"):
            ru_variants = extract_variants(r["ru"])
            if ru_variants and not any(ru_variant_in_sentence(v, r["ex_ru"]) for v in ru_variants):
                missing_fields.append("ex_ru")

        if missing_fields:
            bad.append({
                "number": r["number"],
                "lesson": r["lesson"],
                "nl": r["nl"],
                "en": r["en"],
                "ru": r["ru"],
                "missing": missing_fields,
            })
        else:
            valid.append(r)

    return valid, bad

# ---------------- ПАРСИНГ CSV ----------------
def parse_csv_to_rows(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
            f.seek(0)
        except Exception:
            dialect = csv.excel

        reader = csv.reader(f, dialect)
        raw_headers = next(reader, None)
        if not raw_headers:
            raise ValueError("Пустой файл или отсутствует строка заголовков.")

        headers = [normalize_header(h) for h in raw_headers]
        seen = _seen_headers_str(headers)

        rows: List[Dict[str, str]] = []
        last_lesson = ""

        for lineno, row in enumerate(reader, start=2):
            if not any((cell or "").strip() for cell in row):
                continue

            rec_raw: Dict[str, str] = {
                headers[i]: (row[i].strip() if i < len(headers) else "")
                for i in range(len(headers))
            }

            number_val = rec_raw.get("number", "")
            lesson_val = rec_raw.get("lesson", "")

            # если в number пришло "1.1 Familie (1)" — отделим урок
            if number_val and not lesson_val:
                n_split, l_split = split_number_and_lesson(number_val)
                if l_split:
                    number_val, lesson_val = n_split, l_split

            if not lesson_val:
                lesson_val = last_lesson

            # обязательные поля
            missing = [k for k in REQUIRED_KEYS_MIN if not (rec_raw.get(k) or (k == "number" and number_val))]
            if missing:
                human = ", ".join(missing)
                raise ValueError(
                    f"Строка {lineno}: отсутствуют обязательные поля ({human}). "
                    f"Обнаруженные заголовки: {seen}"
                )

            if lesson_val:
                last_lesson = lesson_val

            record = {
                "lesson": lesson_val or "",
                "number": number_val or rec_raw.get("number", ""),
                "nl": rec_raw.get("nl", ""),
                "en": rec_raw.get("en", ""),
                "ru": rec_raw.get("ru", ""),
                "ex_nl": rec_raw.get("ex_nl", ""),
                "ex_en": rec_raw.get("ex_en", ""),
                "ex_ru": rec_raw.get("ex_ru", ""),
                "audio_nl": rec_raw.get("audio_nl", ""),
                "audio_en": rec_raw.get("audio_en", ""),
                "audio_ru": rec_raw.get("audio_ru", ""),
            }
            rows.append(record)

        if not rows:
            raise ValueError(f"Не найдено ни одной непустой строки. Заголовки: {seen}")

        return rows


