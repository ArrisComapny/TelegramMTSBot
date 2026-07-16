import re
import email as email_lib
import imaplib
import asyncio

from bs4 import BeautifulSoup
from email.message import Message
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

# Параметры получения кода
IMAP_SERVER = "imap.yandex.com"
SUBJECT_FILTER = "Ozon"        # фильтр по теме письма ("" — брать любые письма)
CODE_MAX_AGE_SECONDS = 180     # код считается свежим, если письмо не старше 3 минут
FETCH_LAST_N = 10              # сколько последних писем проверяем

MSK_TZ = timezone(timedelta(hours=3))


class YandexMailClient:
    """
    IMAP-клиент для Yandex.Почты.
    Подключается по адресу почты и токену (паролю приложения) и достаёт
    последний свежий код подтверждения из входящих.

    Перенесён из проекта DesktopBrowser и отвязан от его базы данных:
    метод возвращает код напрямую, ничего не пишет в БД.
    """

    def __init__(self, mail: str, token: str) -> None:
        self.imap_server = IMAP_SERVER
        self.email_account = mail  # Адрес почты
        self.password = token      # Пароль приложения (токен)
        self.mail = None           # IMAP-сессия

    def connect(self) -> None:
        """Подключение к почтовому серверу и авторизация"""
        self.mail = imaplib.IMAP4_SSL(self.imap_server)
        self.mail.login(self.email_account, self.password)

    @staticmethod
    def decode_mime_header(header: str) -> str:
        """Декодирует MIME-заголовки писем"""
        decoded_parts = decode_header(header)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                part = part.decode(encoding or "utf-8", errors="ignore")
            result.append(part)
        return "".join(result)

    @staticmethod
    def get_code(msg: Message) -> str | None:
        """Извлекает 6-значный код из тела письма. Удаляет ссылки, изображения, лишние пробелы."""
        email_body = None
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload is not None:
                        email_body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
        else:
            payload = msg.get_payload(decode=True)
            if payload is not None:
                email_body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")

        if not email_body:
            return None

        soup = BeautifulSoup(email_body, "html.parser")
        text = soup.get_text()

        text = re.sub(r"http[s]?://\S+", "", text)   # Удаление ссылок
        text = re.sub(r"\[image:.*?\]", "", text)     # Удаление изображений
        text = re.sub(r"\s+", " ", text).strip()      # Сжатие пробелов

        match = re.search(r"\b\d{6}\b", text)         # Поиск 6-значного кода
        if match:
            return match.group(0)
        return None

    def fetch_code(self, max_age_seconds: int = CODE_MAX_AGE_SECONDS) -> str | None:
        """
        Проверяет последние письма и возвращает самый свежий код подтверждения.
        Если подходящего письма (нужная тема + не старше max_age_seconds) нет — возвращает None.
        """
        now = datetime.now(MSK_TZ).replace(tzinfo=None)

        self.mail.select("inbox")
        status, messages = self.mail.search(None, "ALL")
        if status != "OK":
            raise RuntimeError("Не удалось выполнить поиск писем")

        candidates = []
        for num in messages[0].split()[-FETCH_LAST_N:]:  # последние N писем
            status, data = self.mail.fetch(num, "(RFC822)")
            if status != "OK" or not data or not data[0]:
                continue

            msg = email_lib.message_from_bytes(data[0][1])

            subject = self.decode_mime_header(msg.get("Subject", ""))
            if SUBJECT_FILTER and SUBJECT_FILTER.lower() not in subject.lower():
                continue

            # Дата письма → московское время без tz
            raw_date = msg.get("Date")
            try:
                email_time = parsedate_to_datetime(raw_date)
            except (TypeError, ValueError):
                continue
            if email_time is None:
                continue
            if email_time.tzinfo is None:
                email_time = email_time.replace(tzinfo=timezone.utc)
            email_time = email_time.astimezone(MSK_TZ).replace(tzinfo=None)

            if (now - email_time).total_seconds() > max_age_seconds:
                continue  # письмо слишком старое

            code = self.get_code(msg)
            if code:
                candidates.append((email_time, code))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])  # самый свежий — последним
        return candidates[-1][1]

    def close(self) -> None:
        """Завершение IMAP-сессии"""
        if self.mail is not None:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.mail = None


def _get_code_blocking(mail: str, token: str, max_age_seconds: int) -> str | None:
    client = YandexMailClient(mail=mail, token=token)
    try:
        client.connect()
        return client.fetch_code(max_age_seconds=max_age_seconds)
    finally:
        client.close()


async def get_shop_code(mail: str, token: str,
                        max_age_seconds: int = CODE_MAX_AGE_SECONDS) -> str | None:
    """
    Асинхронная обёртка: получает код из почты магазина.
    imaplib блокирующий, поэтому работа выполняется в отдельном потоке,
    чтобы не блокировать event loop бота.

    Возвращает строку с кодом или None, если свежего кода нет.
    Пробрасывает исключения при ошибке подключения/авторизации.
    """
    return await asyncio.to_thread(_get_code_blocking, mail, token, max_age_seconds)
