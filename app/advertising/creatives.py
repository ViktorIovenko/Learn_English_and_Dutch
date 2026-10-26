"""Safe handling of advertiser material.

Code copied from Awin "My Creative" is never stored for rendering as HTML:
it is parsed, only the tracking link, image URL, size and alt text are kept,
and the client builds its own ``<a><img></a>`` from those values. Scripts,
iframes, event handlers, styles and unknown hosts are rejected.
"""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit

from config import Config
from app.advertising.store import SIZES

# Awin tracking/click and creative hosts (subdomains included).
CLICK_HOSTS = ("awin1.com", "tidd.ly")
IMAGE_HOSTS = ("awin1.com", "awin.com", "awin.net", "awin1.net")

ALLOWED_TAGS = {"a", "img", "br"}


class CreativeError(ValueError):
    """Rejected material; ``str(exc)`` is a short machine-readable code."""


def _host_allowed(host: str, allowed: tuple[str, ...]) -> bool:
    host = (host or "").lower().rstrip(".")
    return any(host == base or host.endswith("." + base) for base in allowed)


def image_hosts() -> tuple[str, ...]:
    extra = tuple(h.strip().lower() for h in str(Config.AWIN_EXTRA_IMAGE_HOSTS or "").split(",") if h.strip())
    return IMAGE_HOSTS + extra


def safe_url(value: str, allowed: tuple[str, ...], error: str) -> str:
    """HTTPS URL on an allowed host; plain http on an allowed host is upgraded."""
    raw = str(value or "").strip().replace("&amp;", "&")
    if not raw or any(ch in raw for ch in "\"'<>\\ \t\r\n"):
        raise CreativeError(error)
    parts = urlsplit(raw)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
        raise CreativeError(error)
    if not _host_allowed(parts.hostname, allowed):
        raise CreativeError(error)
    return urlunsplit(("https", parts.netloc, parts.path, parts.query, parts.fragment))[:2000]


def click_url(value: str) -> str:
    return safe_url(value, CLICK_HOSTS, "click_url_not_awin")


def image_url(value: str) -> str:
    return safe_url(value, image_hosts(), "image_host_not_allowed")


class _CreativeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.text: list[str] = []
        self.error = ""

    def handle_starttag(self, tag, attrs):
        self._tag(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._tag(tag, attrs)

    def _tag(self, tag, attrs):
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            self.error = self.error or f"tag_not_allowed:{tag}"
            return
        values: dict[str, str] = {}
        for name, value in attrs:
            name = (name or "").lower()
            if name.startswith("on") or name in ("style", "srcset", "formaction"):
                self.error = self.error or f"attribute_not_allowed:{name}"
            values[name] = value or ""
        if tag == "a":
            self.links.append(values)
        elif tag == "img":
            self.images.append(values)

    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())

    def handle_comment(self, data):
        pass  # Awin snippets may carry an "<!-- START ... -->" marker

    def handle_decl(self, decl):
        self.error = self.error or "declaration_not_allowed"

    def unknown_decl(self, data):
        self.error = self.error or "declaration_not_allowed"


def parse_awin_creative(code: str) -> dict:
    """Extract a single linked banner image from Awin "My Creative" code."""
    code = str(code or "").strip()
    if not code:
        raise CreativeError("empty_code")
    if len(code) > 5000:
        raise CreativeError("code_too_long")
    lowered = code.lower()
    for marker in ("javascript:", "<script", "<iframe", "data:", "vbscript:", "<style", "<object", "<embed"):
        if marker in lowered:
            raise CreativeError("unsafe_code")
    parser = _CreativeParser()
    parser.feed(code)
    parser.close()
    if parser.error:
        raise CreativeError(parser.error)
    if len(parser.links) != 1 or len(parser.images) != 1:
        raise CreativeError("expected_one_link_and_one_image")
    link, image = parser.links[0], parser.images[0]
    try:
        width = int(str(image.get("width") or "0").strip().rstrip("px"))
        height = int(str(image.get("height") or "0").strip().rstrip("px"))
    except ValueError:
        width = height = 0
    return {
        "click_url": click_url(link.get("href", "")),
        "image_url": image_url(image.get("src", "")),
        "width": width or None,
        "height": height or None,
        "alt": (image.get("alt") or image.get("title") or "")[:200],
    }


def size_key(width, height) -> str:
    key = f"{width}x{height}"
    return key if key in SIZES else ""


# ------------------------------------------------------------ demo banners

# Realistic but obviously fictional advertisers; rendered locally from text,
# so PREVIEW never loads anything from outside.
DEMO_CREATIVES = (
    {"id": "demo-books", "advertiser": "Demo · Book shop", "topics": ["books", "language"], "tone": "amber"},
    {"id": "demo-course", "advertiser": "Demo · Online course", "topics": ["education", "language"], "tone": "violet"},
    {"id": "demo-travel", "advertiser": "Demo · Travel", "topics": ["travel"], "tone": "teal"},
)

_DEMO_TEXT = {
    "demo-books": {
        "en": ("Graded readers for every level", "Short stories in 10 languages", "Shop now"),
        "ru": ("Адаптированные книги для любого уровня", "Короткие истории на 10 языках", "В магазин"),
        "nl": ("Leesboeken voor elk niveau", "Korte verhalen in 10 talen", "Bekijk"),
        "de": ("Lektüren für jedes Niveau", "Kurzgeschichten in 10 Sprachen", "Ansehen"),
        "fr": ("Lectures graduées pour tous niveaux", "Histoires courtes en 10 langues", "Voir"),
        "es": ("Lecturas graduadas para cada nivel", "Relatos cortos en 10 idiomas", "Ver"),
        "it": ("Letture graduate per ogni livello", "Racconti brevi in 10 lingue", "Scopri"),
        "pt": ("Leituras graduadas para cada nível", "Contos curtos em 10 idiomas", "Ver"),
        "pl": ("Lektury na każdym poziomie", "Krótkie historie w 10 językach", "Zobacz"),
        "uk": ("Адаптовані книжки для будь-якого рівня", "Короткі історії 10 мовами", "Переглянути"),
    },
    "demo-course": {
        "en": ("Speak with confidence", "Live conversation classes online", "Learn more"),
        "ru": ("Говорите уверенно", "Разговорные онлайн-занятия", "Подробнее"),
        "nl": ("Spreek met vertrouwen", "Live conversatielessen online", "Meer info"),
        "de": ("Sicher sprechen", "Live-Konversationskurse online", "Mehr erfahren"),
        "fr": ("Parlez avec assurance", "Cours de conversation en direct", "En savoir plus"),
        "es": ("Habla con confianza", "Clases de conversación en vivo", "Más info"),
        "it": ("Parla con sicurezza", "Lezioni di conversazione dal vivo", "Scopri di più"),
        "pt": ("Fale com confiança", "Aulas de conversação ao vivo", "Saiba mais"),
        "pl": ("Mów pewnie", "Zajęcia konwersacyjne na żywo", "Więcej"),
        "uk": ("Говоріть упевнено", "Розмовні онлайн-заняття", "Детальніше"),
    },
    "demo-travel": {
        "en": ("Practise abroad", "City trips for language learners", "Explore"),
        "ru": ("Практика за границей", "Поездки для изучающих языки", "Смотреть"),
        "nl": ("Oefen in het buitenland", "Stedentrips voor taalleerders", "Ontdek"),
        "de": ("Im Ausland üben", "Städtereisen für Sprachlernende", "Entdecken"),
        "fr": ("Pratiquez à l'étranger", "Séjours pour apprenants", "Découvrir"),
        "es": ("Practica en el extranjero", "Viajes para estudiantes de idiomas", "Explorar"),
        "it": ("Pratica all'estero", "Viaggi per chi studia lingue", "Esplora"),
        "pt": ("Pratique no exterior", "Viagens para estudantes de idiomas", "Explorar"),
        "pl": ("Ćwicz za granicą", "Wyjazdy dla uczących się języków", "Odkryj"),
        "uk": ("Практика за кордоном", "Поїздки для тих, хто вивчає мови", "Дивитися"),
    },
}

AD_LABEL = {
    "en": "Ad", "ru": "Реклама", "nl": "Advertentie", "de": "Anzeige", "fr": "Publicité",
    "es": "Anuncio", "it": "Pubblicità", "pt": "Anúncio", "pl": "Reklama", "uk": "Реклама",
}
PREVIEW_LABEL = "Ad Preview"

CONSENT_TEXT = {
    "en": ("Partner offers", "We can show offers from Awin partners. They may set cookies when shown or clicked. No learning data is shared.", "Allow", "No thanks"),
    "ru": ("Предложения партнёров", "Мы можем показывать предложения партнёров Awin. При показе или клике они могут устанавливать cookies. Учебные данные не передаются.", "Разрешить", "Нет, спасибо"),
    "nl": ("Partneraanbiedingen", "We kunnen aanbiedingen van Awin-partners tonen. Zij kunnen cookies plaatsen bij weergave of klik. Leergegevens worden niet gedeeld.", "Toestaan", "Nee, bedankt"),
    "de": ("Partnerangebote", "Wir können Angebote von Awin-Partnern zeigen. Diese können beim Anzeigen oder Klicken Cookies setzen. Lerndaten werden nicht geteilt.", "Erlauben", "Nein, danke"),
    "fr": ("Offres partenaires", "Nous pouvons afficher des offres de partenaires Awin. Ils peuvent déposer des cookies à l'affichage ou au clic. Aucune donnée d'apprentissage n'est partagée.", "Autoriser", "Non merci"),
    "es": ("Ofertas de socios", "Podemos mostrar ofertas de socios de Awin. Pueden usar cookies al mostrarse o al hacer clic. No se comparten datos de aprendizaje.", "Permitir", "No, gracias"),
    "it": ("Offerte dei partner", "Possiamo mostrare offerte dei partner Awin. Possono impostare cookie alla visualizzazione o al clic. Nessun dato di studio viene condiviso.", "Consenti", "No, grazie"),
    "pt": ("Ofertas de parceiros", "Podemos mostrar ofertas de parceiros Awin. Eles podem definir cookies ao exibir ou clicar. Nenhum dado de estudo é partilhado.", "Permitir", "Não, obrigado"),
    "pl": ("Oferty partnerów", "Możemy pokazywać oferty partnerów Awin. Mogą ustawiać pliki cookie przy wyświetleniu lub kliknięciu. Dane z nauki nie są udostępniane.", "Zezwól", "Nie, dziękuję"),
    "uk": ("Пропозиції партнерів", "Ми можемо показувати пропозиції партнерів Awin. Під час показу чи кліку вони можуть встановлювати cookies. Навчальні дані не передаються.", "Дозволити", "Ні, дякую"),
}


def lang(code: str) -> str:
    code = str(code or "").lower()[:2]
    return code if code in AD_LABEL else "en"


def demo_text(demo_id: str, language: str) -> tuple[str, str, str]:
    texts = _DEMO_TEXT.get(demo_id, _DEMO_TEXT["demo-course"])
    return texts.get(lang(language), texts["en"])
