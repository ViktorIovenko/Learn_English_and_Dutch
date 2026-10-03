from __future__ import annotations

import sqlite3
import time
from contextlib import closing

from app.i18n import SUPPORTED_UI_LANGUAGES


LANGUAGE_LABELS = {
    "en": "English",
    "ru": "Русский",
    "nl": "Nederlands",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "pl": "Polski",
    "uk": "Українська",
}


ONBOARDING_TEXT = {
    "en": {
        "choose_language": "Choose the app interface language:",
        "choose_account": "What type of account do you need?",
        "standard_account": "👤 Regular account",
        "child_account": "🧒 Child account",
        "completed": "✅ Registration is complete. You can now open the app.",
        "choose_language_first": "Please choose the app interface language first.",
        "invalid_choice": "This option is not available. Please try again.",
        "identity_required": "Set a name or username in Telegram, then press /start again.",
        "pairing_caption": "Ask a parent to scan this QR code or send them the link below. The link is valid for 10 minutes.\n\n{url}\n\nNew link: /family",
        "pairing_child_only": "A parent link is available only for a child account.",
        "pairing_invalid": "This parent link is invalid or has expired. Ask the child to create a new one with /family.",
        "pairing_parent_required": "Only a regular account can be connected as a parent.",
        "pairing_parent_limit": "This child already has 5 connected adults. Remove one connection before adding another.",
        "pairing_linked": "✅ Child account {name} is now connected to your account.",
        "pairing_confirm": "Connect child account {name} to your account?",
        "pairing_confirm_button": "✅ Connect",
        "pairing_cancel_button": "❌ Cancel",
        "pairing_cancelled": "Connection cancelled.",
        "pairing_parent_only": "A child invite link is available only for a regular (parent) account.",
        "pairing_child_required": "Only a child account can accept a parent's invite.",
        "invite_caption": "Ask your child to scan this QR code or send them the link below. The link is valid for 10 minutes.\n\n{url}\n\nNew link: /family",
        "pairing_join_confirm": "Connect your account to parent {name}?",
        "pairing_joined": "✅ Your account is now connected to parent {name}.",
    },
    "ru": {
        "choose_language": "Выберите язык интерфейса приложения:",
        "choose_account": "Какой аккаунт вам нужен?",
        "standard_account": "👤 Обычный аккаунт",
        "child_account": "🧒 Детский аккаунт",
        "completed": "✅ Регистрация завершена. Теперь можно открыть приложение.",
        "choose_language_first": "Сначала выберите язык интерфейса приложения.",
        "invalid_choice": "Этот вариант недоступен. Попробуйте ещё раз.",
        "identity_required": "Укажите имя или username в Telegram, затем снова нажмите /start.",
        "pairing_caption": "Попросите родителя отсканировать QR-код или отправьте ему ссылку ниже. Ссылка действует 10 минут.\n\n{url}\n\nНовая ссылка: /family",
        "pairing_child_only": "Ссылка для родителя доступна только детскому аккаунту.",
        "pairing_invalid": "Ссылка недействительна или устарела. Попросите ребёнка создать новую командой /family.",
        "pairing_parent_required": "Подключиться как родитель может только обычный аккаунт.",
        "pairing_parent_limit": "К ребёнку уже подключено 5 взрослых. Перед добавлением нового нужно удалить одну связь.",
        "pairing_linked": "✅ Детский аккаунт {name} подключён к вашему аккаунту.",
        "pairing_confirm": "Подключить детский аккаунт {name} к вашему аккаунту?",
        "pairing_confirm_button": "✅ Подключить",
        "pairing_cancel_button": "❌ Отмена",
        "pairing_cancelled": "Подключение отменено.",
        "pairing_parent_only": "Ссылка-приглашение для ребёнка доступна только обычному (родительскому) аккаунту.",
        "pairing_child_required": "Принять приглашение родителя может только детский аккаунт.",
        "invite_caption": "Попросите ребёнка отсканировать QR-код или отправьте ему ссылку ниже. Ссылка действует 10 минут.\n\n{url}\n\nНовая ссылка: /family",
        "pairing_join_confirm": "Подключить ваш аккаунт к родителю {name}?",
        "pairing_joined": "✅ Ваш аккаунт подключён к родителю {name}.",
    },
    "nl": {
        "choose_language": "Kies de interfacetaal van de app:",
        "choose_account": "Welk type account heb je nodig?",
        "standard_account": "👤 Normaal account",
        "child_account": "🧒 Kinderaccount",
        "completed": "✅ De registratie is voltooid. Je kunt de app nu openen.",
        "choose_language_first": "Kies eerst de interfacetaal van de app.",
        "invalid_choice": "Deze optie is niet beschikbaar. Probeer het opnieuw.",
        "identity_required": "Stel een naam of gebruikersnaam in Telegram in en druk opnieuw op /start.",
        "pairing_caption": "Laat een ouder deze QR-code scannen of stuur de onderstaande link. De link is 10 minuten geldig.\n\n{url}\n\nNieuwe link: /family",
        "pairing_child_only": "Een ouderlink is alleen beschikbaar voor een kinderaccount.",
        "pairing_invalid": "Deze link is ongeldig of verlopen. Vraag het kind om met /family een nieuwe link te maken.",
        "pairing_parent_required": "Alleen een normaal account kan als ouder worden gekoppeld.",
        "pairing_parent_limit": "Dit kind heeft al 5 gekoppelde volwassenen. Verwijder eerst een koppeling.",
        "pairing_linked": "✅ Kinderaccount {name} is aan je account gekoppeld.",
        "pairing_confirm": "Kinderaccount {name} aan je account koppelen?",
        "pairing_confirm_button": "✅ Koppelen",
        "pairing_cancel_button": "❌ Annuleren",
        "pairing_cancelled": "Koppeling geannuleerd.",
        "pairing_parent_only": "Een uitnodigingslink voor een kind is alleen beschikbaar voor een normaal (ouder)account.",
        "pairing_child_required": "Alleen een kinderaccount kan de uitnodiging van een ouder accepteren.",
        "invite_caption": "Laat je kind deze QR-code scannen of stuur de onderstaande link. De link is 10 minuten geldig.\n\n{url}\n\nNieuwe link: /family",
        "pairing_join_confirm": "Je account koppelen aan ouder {name}?",
        "pairing_joined": "✅ Je account is nu gekoppeld aan ouder {name}.",
    },
    "de": {
        "choose_language": "Wähle die Sprache der App-Oberfläche:",
        "choose_account": "Welche Art von Konto benötigst du?",
        "standard_account": "👤 Normales Konto",
        "child_account": "🧒 Kinderkonto",
        "completed": "✅ Die Registrierung ist abgeschlossen. Du kannst die App jetzt öffnen.",
        "choose_language_first": "Wähle zuerst die Sprache der App-Oberfläche.",
        "invalid_choice": "Diese Option ist nicht verfügbar. Bitte versuche es erneut.",
        "identity_required": "Lege in Telegram einen Namen oder Benutzernamen fest und drücke erneut auf /start.",
        "pairing_caption": "Lass einen Elternteil diesen QR-Code scannen oder sende den Link unten. Der Link ist 10 Minuten gültig.\n\n{url}\n\nNeuer Link: /family",
        "pairing_child_only": "Ein Eltern-Link ist nur für ein Kinderkonto verfügbar.",
        "pairing_invalid": "Dieser Link ist ungültig oder abgelaufen. Bitte das Kind, mit /family einen neuen Link zu erstellen.",
        "pairing_parent_required": "Nur ein normales Konto kann als Elternkonto verbunden werden.",
        "pairing_parent_limit": "Mit diesem Kind sind bereits 5 Erwachsene verbunden. Entferne zuerst eine Verbindung.",
        "pairing_linked": "✅ Das Kinderkonto {name} wurde mit deinem Konto verbunden.",
        "pairing_confirm": "Das Kinderkonto {name} mit deinem Konto verbinden?",
        "pairing_confirm_button": "✅ Verbinden",
        "pairing_cancel_button": "❌ Abbrechen",
        "pairing_cancelled": "Verbindung abgebrochen.",
        "pairing_parent_only": "Ein Einladungslink für ein Kind ist nur für ein normales (Eltern-)Konto verfügbar.",
        "pairing_child_required": "Nur ein Kinderkonto kann die Einladung eines Elternteils annehmen.",
        "invite_caption": "Lass dein Kind diesen QR-Code scannen oder sende den Link unten. Der Link ist 10 Minuten gültig.\n\n{url}\n\nNeuer Link: /family",
        "pairing_join_confirm": "Dein Konto mit Elternteil {name} verbinden?",
        "pairing_joined": "✅ Dein Konto ist jetzt mit Elternteil {name} verbunden.",
    },
    "fr": {
        "choose_language": "Choisissez la langue de l’interface de l’application :",
        "choose_account": "De quel type de compte avez-vous besoin ?",
        "standard_account": "👤 Compte standard",
        "child_account": "🧒 Compte enfant",
        "completed": "✅ L’inscription est terminée. Vous pouvez maintenant ouvrir l’application.",
        "choose_language_first": "Choisissez d’abord la langue de l’interface de l’application.",
        "invalid_choice": "Cette option n’est pas disponible. Veuillez réessayer.",
        "identity_required": "Définissez un nom ou un nom d’utilisateur dans Telegram, puis appuyez à nouveau sur /start.",
        "pairing_caption": "Demandez à un parent de scanner ce QR code ou envoyez-lui le lien ci-dessous. Le lien est valable 10 minutes.\n\n{url}\n\nNouveau lien : /family",
        "pairing_child_only": "Le lien parent est disponible uniquement pour un compte enfant.",
        "pairing_invalid": "Ce lien est invalide ou expiré. Demandez à l’enfant d’en créer un nouveau avec /family.",
        "pairing_parent_required": "Seul un compte standard peut être connecté comme parent.",
        "pairing_parent_limit": "Cet enfant a déjà 5 adultes connectés. Supprimez d’abord une connexion.",
        "pairing_linked": "✅ Le compte enfant {name} est maintenant connecté à votre compte.",
        "pairing_confirm": "Connecter le compte enfant {name} à votre compte ?",
        "pairing_confirm_button": "✅ Connecter",
        "pairing_cancel_button": "❌ Annuler",
        "pairing_cancelled": "Connexion annulée.",
        "pairing_parent_only": "Un lien d’invitation pour un enfant est disponible uniquement pour un compte standard (parent).",
        "pairing_child_required": "Seul un compte enfant peut accepter l’invitation d’un parent.",
        "invite_caption": "Demandez à votre enfant de scanner ce QR code ou envoyez-lui le lien ci-dessous. Le lien est valable 10 minutes.\n\n{url}\n\nNouveau lien : /family",
        "pairing_join_confirm": "Connecter votre compte au parent {name} ?",
        "pairing_joined": "✅ Votre compte est maintenant connecté au parent {name}.",
    },
    "es": {
        "choose_language": "Elige el idioma de la interfaz de la aplicación:",
        "choose_account": "¿Qué tipo de cuenta necesitas?",
        "standard_account": "👤 Cuenta normal",
        "child_account": "🧒 Cuenta infantil",
        "completed": "✅ El registro ha finalizado. Ya puedes abrir la aplicación.",
        "choose_language_first": "Primero elige el idioma de la interfaz de la aplicación.",
        "invalid_choice": "Esta opción no está disponible. Inténtalo de nuevo.",
        "identity_required": "Configura un nombre o nombre de usuario en Telegram y vuelve a pulsar /start.",
        "pairing_caption": "Pide a un progenitor que escanee este código QR o envíale el enlace. Es válido durante 10 minutos.\n\n{url}\n\nNuevo enlace: /family",
        "pairing_child_only": "El enlace para progenitores solo está disponible en una cuenta infantil.",
        "pairing_invalid": "Este enlace no es válido o ha caducado. Pide al menor que cree otro con /family.",
        "pairing_parent_required": "Solo una cuenta normal puede conectarse como progenitor.",
        "pairing_parent_limit": "Este menor ya tiene 5 adultos conectados. Elimina primero una conexión.",
        "pairing_linked": "✅ La cuenta infantil {name} está conectada a tu cuenta.",
        "pairing_confirm": "¿Conectar la cuenta infantil {name} a tu cuenta?",
        "pairing_confirm_button": "✅ Conectar",
        "pairing_cancel_button": "❌ Cancelar",
        "pairing_cancelled": "Conexión cancelada.",
        "pairing_parent_only": "Un enlace de invitación para un hijo solo está disponible en una cuenta normal (de progenitor).",
        "pairing_child_required": "Solo una cuenta infantil puede aceptar la invitación de un progenitor.",
        "invite_caption": "Pide a tu hijo que escanee este código QR o envíale el enlace. Es válido durante 10 minutos.\n\n{url}\n\nNuevo enlace: /family",
        "pairing_join_confirm": "¿Conectar tu cuenta con el progenitor {name}?",
        "pairing_joined": "✅ Tu cuenta ahora está conectada con el progenitor {name}.",
    },
    "it": {
        "choose_language": "Scegli la lingua dell’interfaccia dell’app:",
        "choose_account": "Di quale tipo di account hai bisogno?",
        "standard_account": "👤 Account normale",
        "child_account": "🧒 Account bambino",
        "completed": "✅ La registrazione è completata. Ora puoi aprire l’app.",
        "choose_language_first": "Prima scegli la lingua dell’interfaccia dell’app.",
        "invalid_choice": "Questa opzione non è disponibile. Riprova.",
        "identity_required": "Imposta un nome o un nome utente in Telegram, quindi premi di nuovo /start.",
        "pairing_caption": "Chiedi a un genitore di scansionare questo codice QR o inviagli il link. È valido per 10 minuti.\n\n{url}\n\nNuovo link: /family",
        "pairing_child_only": "Il link per il genitore è disponibile solo per un account bambino.",
        "pairing_invalid": "Questo link non è valido o è scaduto. Chiedi al bambino di crearne uno nuovo con /family.",
        "pairing_parent_required": "Solo un account normale può essere collegato come genitore.",
        "pairing_parent_limit": "Questo bambino ha già 5 adulti collegati. Rimuovi prima un collegamento.",
        "pairing_linked": "✅ L’account bambino {name} è ora collegato al tuo account.",
        "pairing_confirm": "Collegare l’account bambino {name} al tuo account?",
        "pairing_confirm_button": "✅ Collega",
        "pairing_cancel_button": "❌ Annulla",
        "pairing_cancelled": "Collegamento annullato.",
        "pairing_parent_only": "Un link di invito per un figlio è disponibile solo per un account normale (genitore).",
        "pairing_child_required": "Solo un account bambino può accettare l’invito di un genitore.",
        "invite_caption": "Chiedi a tuo figlio di scansionare questo codice QR o inviagli il link. È valido per 10 minuti.\n\n{url}\n\nNuovo link: /family",
        "pairing_join_confirm": "Collegare il tuo account al genitore {name}?",
        "pairing_joined": "✅ Il tuo account è ora collegato al genitore {name}.",
    },
    "pt": {
        "choose_language": "Escolha o idioma da interface da aplicação:",
        "choose_account": "De que tipo de conta precisa?",
        "standard_account": "👤 Conta normal",
        "child_account": "🧒 Conta infantil",
        "completed": "✅ O registo foi concluído. Já pode abrir a aplicação.",
        "choose_language_first": "Primeiro escolha o idioma da interface da aplicação.",
        "invalid_choice": "Esta opção não está disponível. Tente novamente.",
        "identity_required": "Defina um nome ou nome de utilizador no Telegram e prima /start novamente.",
        "pairing_caption": "Peça a um responsável para ler este código QR ou envie-lhe o link. É válido durante 10 minutos.\n\n{url}\n\nNovo link: /family",
        "pairing_child_only": "O link para o responsável só está disponível numa conta infantil.",
        "pairing_invalid": "Este link é inválido ou expirou. Peça à criança para criar outro com /family.",
        "pairing_parent_required": "Apenas uma conta normal pode ser ligada como responsável.",
        "pairing_parent_limit": "Esta criança já tem 5 adultos ligados. Remova primeiro uma ligação.",
        "pairing_linked": "✅ A conta infantil {name} está agora ligada à sua conta.",
        "pairing_confirm": "Ligar a conta infantil {name} à sua conta?",
        "pairing_confirm_button": "✅ Ligar",
        "pairing_cancel_button": "❌ Cancelar",
        "pairing_cancelled": "Ligação cancelada.",
        "pairing_parent_only": "Um link de convite para um filho só está disponível numa conta normal (de responsável).",
        "pairing_child_required": "Apenas uma conta infantil pode aceitar o convite de um responsável.",
        "invite_caption": "Peça ao seu filho para ler este código QR ou envie-lhe o link. É válido durante 10 minutos.\n\n{url}\n\nNovo link: /family",
        "pairing_join_confirm": "Ligar a sua conta ao responsável {name}?",
        "pairing_joined": "✅ A sua conta está agora ligada ao responsável {name}.",
    },
    "pl": {
        "choose_language": "Wybierz język interfejsu aplikacji:",
        "choose_account": "Jakiego typu konta potrzebujesz?",
        "standard_account": "👤 Zwykłe konto",
        "child_account": "🧒 Konto dziecka",
        "completed": "✅ Rejestracja została zakończona. Możesz teraz otworzyć aplikację.",
        "choose_language_first": "Najpierw wybierz język interfejsu aplikacji.",
        "invalid_choice": "Ta opcja jest niedostępna. Spróbuj ponownie.",
        "identity_required": "Ustaw nazwę lub nazwę użytkownika w Telegramie, a następnie ponownie naciśnij /start.",
        "pairing_caption": "Poproś rodzica o zeskanowanie tego kodu QR albo wyślij mu poniższy link. Link jest ważny przez 10 minut.\n\n{url}\n\nNowy link: /family",
        "pairing_child_only": "Link dla rodzica jest dostępny tylko dla konta dziecka.",
        "pairing_invalid": "Ten link jest nieprawidłowy lub wygasł. Poproś dziecko o utworzenie nowego przez /family.",
        "pairing_parent_required": "Tylko zwykłe konto może zostać połączone jako konto rodzica.",
        "pairing_parent_limit": "To dziecko ma już 5 połączonych dorosłych. Najpierw usuń jedno połączenie.",
        "pairing_linked": "✅ Konto dziecka {name} zostało połączone z twoim kontem.",
        "pairing_confirm": "Połączyć konto dziecka {name} z twoim kontem?",
        "pairing_confirm_button": "✅ Połącz",
        "pairing_cancel_button": "❌ Anuluj",
        "pairing_cancelled": "Anulowano połączenie.",
        "pairing_parent_only": "Link zaproszenia dla dziecka jest dostępny tylko dla zwykłego konta (rodzica).",
        "pairing_child_required": "Tylko konto dziecka może przyjąć zaproszenie od rodzica.",
        "invite_caption": "Poproś dziecko o zeskanowanie tego kodu QR albo wyślij mu poniższy link. Link jest ważny przez 10 minut.\n\n{url}\n\nNowy link: /family",
        "pairing_join_confirm": "Połączyć twoje konto z rodzicem {name}?",
        "pairing_joined": "✅ Twoje konto jest teraz połączone z rodzicem {name}.",
    },
    "uk": {
        "choose_language": "Виберіть мову інтерфейсу застосунку:",
        "choose_account": "Який тип облікового запису вам потрібен?",
        "standard_account": "👤 Звичайний обліковий запис",
        "child_account": "🧒 Дитячий обліковий запис",
        "completed": "✅ Реєстрацію завершено. Тепер можна відкрити застосунок.",
        "choose_language_first": "Спочатку виберіть мову інтерфейсу застосунку.",
        "invalid_choice": "Цей варіант недоступний. Спробуйте ще раз.",
        "identity_required": "Укажіть ім’я або username у Telegram, а потім знову натисніть /start.",
        "pairing_caption": "Попросіть когось із батьків відсканувати QR-код або надішліть посилання нижче. Воно діє 10 хвилин.\n\n{url}\n\nНове посилання: /family",
        "pairing_child_only": "Посилання для батьків доступне лише дитячому обліковому запису.",
        "pairing_invalid": "Посилання недійсне або застаріло. Попросіть дитину створити нове командою /family.",
        "pairing_parent_required": "Підключитися як хтось із батьків може лише звичайний обліковий запис.",
        "pairing_parent_limit": "До дитини вже підключено 5 дорослих. Спочатку видаліть один зв’язок.",
        "pairing_linked": "✅ Дитячий обліковий запис {name} підключено до вашого облікового запису.",
        "pairing_confirm": "Підключити дитячий обліковий запис {name} до вашого?",
        "pairing_confirm_button": "✅ Підключити",
        "pairing_cancel_button": "❌ Скасувати",
        "pairing_cancelled": "Підключення скасовано.",
        "pairing_parent_only": "Посилання-запрошення для дитини доступне лише звичайному (батьківському) обліковому запису.",
        "pairing_child_required": "Прийняти запрошення від батьків може лише дитячий обліковий запис.",
        "invite_caption": "Попросіть дитину відсканувати QR-код або надішліть їй посилання нижче. Воно діє 10 хвилин.\n\n{url}\n\nНове посилання: /family",
        "pairing_join_confirm": "Підключити ваш обліковий запис до батьків {name}?",
        "pairing_joined": "✅ Ваш обліковий запис підключено до батьків {name}.",
    },
}


LANGUAGE_CONFIRMATION_TEXT = {
    "en": {
        "confirm_detected_language": "Your Telegram interface language is {language}. Use this language for the app too?",
        "confirm_language_yes": "✅ Yes",
        "confirm_language_no": "🌐 Choose another language",
    },
    "ru": {
        "confirm_detected_language": "Язык интерфейса вашего Telegram — {language}. Оставить этот язык для приложения?",
        "confirm_language_yes": "✅ Да",
        "confirm_language_no": "🌐 Выбрать другой язык",
    },
    "nl": {
        "confirm_detected_language": "De interfacetaal van je Telegram is {language}. Deze taal ook voor de app gebruiken?",
        "confirm_language_yes": "✅ Ja",
        "confirm_language_no": "🌐 Een andere taal kiezen",
    },
    "de": {
        "confirm_detected_language": "Die Sprache deiner Telegram-Oberfläche ist {language}. Diese Sprache auch für die App verwenden?",
        "confirm_language_yes": "✅ Ja",
        "confirm_language_no": "🌐 Andere Sprache wählen",
    },
    "fr": {
        "confirm_detected_language": "La langue de votre interface Telegram est {language}. Utiliser aussi cette langue pour l’application ?",
        "confirm_language_yes": "✅ Oui",
        "confirm_language_no": "🌐 Choisir une autre langue",
    },
    "es": {
        "confirm_detected_language": "El idioma de tu interfaz de Telegram es {language}. ¿Usar también este idioma en la aplicación?",
        "confirm_language_yes": "✅ Sí",
        "confirm_language_no": "🌐 Elegir otro idioma",
    },
    "it": {
        "confirm_detected_language": "La lingua dell’interfaccia di Telegram è {language}. Usare questa lingua anche per l’app?",
        "confirm_language_yes": "✅ Sì",
        "confirm_language_no": "🌐 Scegli un’altra lingua",
    },
    "pt": {
        "confirm_detected_language": "O idioma da interface do Telegram é {language}. Usar também este idioma na aplicação?",
        "confirm_language_yes": "✅ Sim",
        "confirm_language_no": "🌐 Escolher outro idioma",
    },
    "pl": {
        "confirm_detected_language": "Język interfejsu Telegrama to {language}. Użyć tego języka również w aplikacji?",
        "confirm_language_yes": "✅ Tak",
        "confirm_language_no": "🌐 Wybierz inny język",
    },
    "uk": {
        "confirm_detected_language": "Мова інтерфейсу вашого Telegram — {language}. Залишити цю мову для застосунку?",
        "confirm_language_yes": "✅ Так",
        "confirm_language_no": "🌐 Вибрати іншу мову",
    },
}


BOT_INTERFACE_TEXT = {
    "en": {
        "menu": "⬇️ Menu",
        "learn_words": "Learn words",
        "upload_words": "Upload words",
        "open_mini_app": "Open mini app",
        "open_browser": "Open in browser",
        "open_app": "Open app",
        "download_android": "Download Android app",
        "login_android": "Sign in to Android app",
        "fresh_login_link": "Fresh sign-in link:",
        "welcome_back": "Welcome back!",
        "trial_ready": "✅ Done! You have 14 days of free access.",
        "password_not_needed": "A password is no longer required. You can use the app.",
        "registration_required": "Register first: send /start.",
        "open_upload_page": "📤 Open upload page",
        "upload_title": "📤 <b>Upload words</b>",
        "upload_help": "Open the page on a computer, paste the words and click Generate.\n\n💡 <i>You can add one word here by simply sending it.</i>",
    },
    "ru": {
        "menu": "⬇️ Меню",
        "learn_words": "Учить слова",
        "upload_words": "Загрузить слова",
        "open_mini_app": "Открыть мини-приложение",
        "open_browser": "Открыть в браузере",
        "open_app": "Открыть приложение",
        "download_android": "Скачать Android-приложение",
        "login_android": "Войти в Android-приложение",
        "fresh_login_link": "Свежая ссылка для входа:",
        "welcome_back": "С возвращением!",
        "trial_ready": "✅ Готово! Вам доступно 14 дней бесплатного пользования.",
        "password_not_needed": "Пароль больше не нужен. Можно пользоваться приложением.",
        "registration_required": "Сначала пройдите регистрацию: отправьте /start.",
        "open_upload_page": "📤 Открыть страницу загрузки", "upload_title": "📤 <b>Загрузка слов</b>",
        "upload_help": "Откройте страницу на компьютере, вставьте слова и нажмите «Сгенерировать».\n\n💡 <i>Одно слово можно добавить здесь, просто отправив его.</i>",
    },
    "nl": {
        "menu": "⬇️ Menu",
        "learn_words": "Woorden leren",
        "upload_words": "Woorden uploaden",
        "open_mini_app": "Mini-app openen",
        "open_browser": "Openen in browser",
        "open_app": "App openen",
        "download_android": "Android-app downloaden",
        "login_android": "Aanmelden bij de Android-app",
        "fresh_login_link": "Nieuwe aanmeldlink:",
        "welcome_back": "Welkom terug!",
        "trial_ready": "✅ Klaar! Je hebt 14 dagen gratis toegang.",
        "password_not_needed": "Een wachtwoord is niet meer nodig. Je kunt de app gebruiken.",
        "registration_required": "Registreer je eerst: stuur /start.",
        "open_upload_page": "📤 Uploadpagina openen", "upload_title": "📤 <b>Woorden uploaden</b>",
        "upload_help": "Open de pagina op een computer, plak de woorden en klik op Genereren.\n\n💡 <i>Je kunt hier één woord toevoegen door het gewoon te sturen.</i>",
    },
    "de": {
        "menu": "⬇️ Menü", "learn_words": "Wörter lernen", "upload_words": "Wörter hochladen",
        "open_mini_app": "Mini-App öffnen", "open_browser": "Im Browser öffnen", "open_app": "App öffnen",
        "download_android": "Android-App herunterladen", "login_android": "In der Android-App anmelden",
        "fresh_login_link": "Neuer Anmeldelink:", "welcome_back": "Willkommen zurück!",
        "trial_ready": "✅ Fertig! Du hast 14 Tage kostenlosen Zugang.",
        "password_not_needed": "Ein Passwort ist nicht mehr erforderlich. Du kannst die App verwenden.",
        "registration_required": "Registriere dich zuerst: Sende /start.", "open_upload_page": "📤 Upload-Seite öffnen", "upload_title": "📤 <b>Wörter hochladen</b>", "upload_help": "Öffne die Seite am Computer, füge die Wörter ein und klicke auf Generieren.\n\n💡 <i>Ein einzelnes Wort kannst du einfach hier senden.</i>",
    },
    "fr": {
        "menu": "⬇️ Menu", "learn_words": "Apprendre des mots", "upload_words": "Importer des mots",
        "open_mini_app": "Ouvrir la mini-application", "open_browser": "Ouvrir dans le navigateur", "open_app": "Ouvrir l’application",
        "download_android": "Télécharger l’application Android", "login_android": "Se connecter à l’application Android",
        "fresh_login_link": "Nouveau lien de connexion :", "welcome_back": "Bon retour !",
        "trial_ready": "✅ Terminé ! Vous disposez de 14 jours d’accès gratuit.",
        "password_not_needed": "Aucun mot de passe n’est désormais requis. Vous pouvez utiliser l’application.",
        "registration_required": "Inscrivez-vous d’abord : envoyez /start.", "open_upload_page": "📤 Ouvrir la page d’import", "upload_title": "📤 <b>Importer des mots</b>", "upload_help": "Ouvrez la page sur un ordinateur, collez les mots et cliquez sur Générer.\n\n💡 <i>Vous pouvez ajouter un mot ici en l’envoyant simplement.</i>",
    },
    "es": {
        "menu": "⬇️ Menú", "learn_words": "Aprender palabras", "upload_words": "Subir palabras",
        "open_mini_app": "Abrir miniaplicación", "open_browser": "Abrir en el navegador", "open_app": "Abrir aplicación",
        "download_android": "Descargar aplicación Android", "login_android": "Iniciar sesión en la aplicación Android",
        "fresh_login_link": "Nuevo enlace de acceso:", "welcome_back": "¡Bienvenido de nuevo!",
        "trial_ready": "✅ Listo. Tienes 14 días de acceso gratuito.",
        "password_not_needed": "Ya no se necesita contraseña. Puedes usar la aplicación.",
        "registration_required": "Regístrate primero: envía /start.", "open_upload_page": "📤 Abrir página de carga", "upload_title": "📤 <b>Subir palabras</b>", "upload_help": "Abre la página en un ordenador, pega las palabras y pulsa Generar.\n\n💡 <i>Puedes añadir una palabra aquí enviándola sin más.</i>",
    },
    "it": {
        "menu": "⬇️ Menu", "learn_words": "Impara le parole", "upload_words": "Carica parole",
        "open_mini_app": "Apri mini app", "open_browser": "Apri nel browser", "open_app": "Apri app",
        "download_android": "Scarica l’app Android", "login_android": "Accedi all’app Android",
        "fresh_login_link": "Nuovo link di accesso:", "welcome_back": "Bentornato!",
        "trial_ready": "✅ Fatto! Hai 14 giorni di accesso gratuito.",
        "password_not_needed": "La password non è più necessaria. Puoi usare l’app.",
        "registration_required": "Prima registrati: invia /start.", "open_upload_page": "📤 Apri pagina di caricamento", "upload_title": "📤 <b>Carica parole</b>", "upload_help": "Apri la pagina su un computer, incolla le parole e fai clic su Genera.\n\n💡 <i>Puoi aggiungere una parola qui semplicemente inviandola.</i>",
    },
    "pt": {
        "menu": "⬇️ Menu", "learn_words": "Aprender palavras", "upload_words": "Carregar palavras",
        "open_mini_app": "Abrir miniaplicação", "open_browser": "Abrir no navegador", "open_app": "Abrir aplicação",
        "download_android": "Transferir aplicação Android", "login_android": "Iniciar sessão na aplicação Android",
        "fresh_login_link": "Novo link de acesso:", "welcome_back": "Bem-vindo de volta!",
        "trial_ready": "✅ Concluído! Tem 14 dias de acesso gratuito.",
        "password_not_needed": "A palavra-passe já não é necessária. Pode usar a aplicação.",
        "registration_required": "Registe-se primeiro: envie /start.", "open_upload_page": "📤 Abrir página de carregamento", "upload_title": "📤 <b>Carregar palavras</b>", "upload_help": "Abra a página num computador, cole as palavras e clique em Gerar.\n\n💡 <i>Pode adicionar uma palavra aqui enviando-a.</i>",
    },
    "pl": {
        "menu": "⬇️ Menu", "learn_words": "Ucz się słów", "upload_words": "Prześlij słowa",
        "open_mini_app": "Otwórz miniaplikację", "open_browser": "Otwórz w przeglądarce", "open_app": "Otwórz aplikację",
        "download_android": "Pobierz aplikację Android", "login_android": "Zaloguj się w aplikacji Android",
        "fresh_login_link": "Nowy link logowania:", "welcome_back": "Witamy ponownie!",
        "trial_ready": "✅ Gotowe! Masz 14 dni bezpłatnego dostępu.",
        "password_not_needed": "Hasło nie jest już potrzebne. Możesz korzystać z aplikacji.",
        "registration_required": "Najpierw się zarejestruj: wyślij /start.", "open_upload_page": "📤 Otwórz stronę przesyłania", "upload_title": "📤 <b>Prześlij słowa</b>", "upload_help": "Otwórz stronę na komputerze, wklej słowa i kliknij Generuj.\n\n💡 <i>Jedno słowo możesz dodać tutaj, po prostu je wysyłając.</i>",
    },
    "uk": {
        "menu": "⬇️ Меню", "learn_words": "Вивчати слова", "upload_words": "Завантажити слова",
        "open_mini_app": "Відкрити мінізастосунок", "open_browser": "Відкрити у браузері", "open_app": "Відкрити застосунок",
        "download_android": "Завантажити Android-застосунок", "login_android": "Увійти в Android-застосунок",
        "fresh_login_link": "Нове посилання для входу:", "welcome_back": "З поверненням!",
        "trial_ready": "✅ Готово! Вам доступно 14 днів безкоштовного доступу.",
        "password_not_needed": "Пароль більше не потрібен. Можна користуватися застосунком.",
        "registration_required": "Спочатку зареєструйтеся: надішліть /start.", "open_upload_page": "📤 Відкрити сторінку завантаження", "upload_title": "📤 <b>Завантаження слів</b>", "upload_help": "Відкрийте сторінку на комп’ютері, вставте слова та натисніть «Згенерувати».\n\n💡 <i>Одне слово можна додати тут, просто надіславши його.</i>",
    },
}


for _language, _texts in LANGUAGE_CONFIRMATION_TEXT.items():
    ONBOARDING_TEXT[_language].update(_texts)


def normalize_telegram_language(language_code: str | None) -> str:
    code = str(language_code or "").strip().lower().split("-", 1)[0].split("_", 1)[0]
    return code if code in SUPPORTED_UI_LANGUAGES else "en"


def onboarding_text(language_code: str | None, key: str, **kwargs: object) -> str:
    language = normalize_telegram_language(language_code)
    text = ONBOARDING_TEXT.get(language, ONBOARDING_TEXT["en"]).get(
        key,
        ONBOARDING_TEXT["en"].get(key, key),
    )
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def bot_interface_text(language_code: str | None, key: str) -> str:
    language = normalize_telegram_language(language_code)
    return BOT_INTERFACE_TEXT.get(language, BOT_INTERFACE_TEXT["en"]).get(
        key,
        BOT_INTERFACE_TEXT["en"].get(key, key),
    )


def bot_interface_values(key: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(texts[key] for texts in BOT_INTERFACE_TEXT.values()))


def ensure_user_settings_schema(db_path: str) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                detected_ui_language TEXT,
                ui_language_override TEXT,
                updated_at INTEGER NOT NULL
            )
        """)
        conn.commit()


def save_detected_language(db_path: str, user_id: int | str, language_code: str | None) -> str:
    language = normalize_telegram_language(language_code)
    ensure_user_settings_schema(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("""
            INSERT INTO user_settings (user_id, detected_ui_language, ui_language_override, updated_at)
            VALUES (?, ?, NULL, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                detected_ui_language=excluded.detected_ui_language,
                updated_at=excluded.updated_at
        """, (str(user_id), language, int(time.time() * 1000)))
        conn.commit()
    return language


def selected_ui_language(db_path: str, user_id: int | str) -> str | None:
    ensure_user_settings_schema(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute(
            "SELECT ui_language_override FROM user_settings WHERE user_id=?",
            (str(user_id),),
        ).fetchone()
    if not row or not row[0]:
        return None
    language = str(row[0]).strip().lower()
    return language if language in SUPPORTED_UI_LANGUAGES else None


def save_selected_ui_language(db_path: str, user_id: int | str, language_code: str) -> bool:
    language = str(language_code or "").strip().lower()
    if language not in SUPPORTED_UI_LANGUAGES:
        return False
    ensure_user_settings_schema(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("""
            INSERT INTO user_settings (user_id, detected_ui_language, ui_language_override, updated_at)
            VALUES (?, NULL, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                ui_language_override=excluded.ui_language_override,
                updated_at=excluded.updated_at
        """, (str(user_id), language, int(time.time() * 1000)))
        conn.commit()
    return True


def account_type(db_path: str, user_id: int | str) -> str | None:
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute(
            "SELECT account_type FROM users WHERE user_id=?",
            (str(user_id),),
        ).fetchone()
    return str(row[0]) if row and row[0] else None


def complete_account_type(db_path: str, user_id: int | str, value: str) -> bool:
    if value not in {"standard", "child"}:
        return False
    with closing(sqlite3.connect(db_path)) as conn:
        cursor = conn.execute(
            "UPDATE users SET account_type=? WHERE user_id=? AND account_type='pending'",
            (value, str(user_id)),
        )
        conn.commit()
    return cursor.rowcount == 1
