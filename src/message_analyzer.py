import re
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class MessageIndicators:
    email_addresses: list[str] = field(default_factory=list)

    urls: list[str] = field(default_factory=list)

    domains: list[str] = field(default_factory=list)

    credential_request: bool = False

    money_request: bool = False

    urgency: bool = False

    threat_language: bool = False

    suspicious_attachment: bool = False

    suspicious_keywords: list[str] = field(
        default_factory=list
    )


class MessageAnalyzer:

    CREDENTIAL_PATTERNS = [
        "password",
        "username",
        "login",
        "log in",
        "sign in",
        "verify your account",
        "verify account",
        "confirm your account",
        "account credentials",
    ]

    MONEY_PATTERNS = [
        "send money",
        "wire transfer",
        "bank transfer",
        "payment",
        "pay immediately",
        "gift card",
        "bank account",
    ]

    URGENCY_PATTERNS = [
        "urgent",
        "immediately",
        "right away",
        "act now",
        "as soon as possible",
        "asap",
        "within 24 hours",
        "today",
    ]

    THREAT_PATTERNS = [
        "account will be suspended",
        "account suspended",
        "account will be closed",
        "account will be disabled",
        "access will be revoked",
        "legal action",
        "unauthorized activity",
    ]

    SUSPICIOUS_EXTENSIONS = [
        ".exe",
        ".scr",
        ".bat",
        ".cmd",
        ".js",
        ".vbs",
        ".ps1",
        ".zip",
    ]


    def analyze(self, message):

        email_addresses = self.extract_emails(
            message
        )

        urls = self.extract_urls(
            message
        )

        domains = self.extract_domains(
            email_addresses,
            urls
        )

        credential_request = (
            self.contains_pattern(
                message,
                self.CREDENTIAL_PATTERNS
            )
        )

        money_request = self.contains_pattern(
            message,
            self.MONEY_PATTERNS
        )

        urgency = self.contains_pattern(
            message,
            self.URGENCY_PATTERNS
        )

        threat_language = self.contains_pattern(
            message,
            self.THREAT_PATTERNS
        )

        suspicious_attachment = (
            self.detect_suspicious_attachment(
                message
            )
        )

        suspicious_keywords = (
            self.collect_suspicious_keywords(
                message
            )
        )

        return MessageIndicators(
            email_addresses=email_addresses,
            urls=urls,
            domains=domains,
            credential_request=credential_request,
            money_request=money_request,
            urgency=urgency,
            threat_language=threat_language,
            suspicious_attachment=suspicious_attachment,
            suspicious_keywords=suspicious_keywords,
        )


    def extract_emails(self, message):

        pattern = (
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+"
            r"\.[A-Za-z]{2,}\b"
        )

        emails = re.findall(
            pattern,
            message
        )

        return list(dict.fromkeys(emails))


    def extract_urls(self, message):

        pattern = r"https?://[^\s<>\"']+"

        urls = re.findall(
            pattern,
            message
        )

        # Remove punctuation that may follow a URL.
        urls = [
            url.rstrip(".,);]")
            for url in urls
        ]

        return list(dict.fromkeys(urls))


    def extract_domains(
        self,
        email_addresses,
        urls
    ):

        domains = []

        for email in email_addresses:

            domain = email.split("@")[-1].lower()

            domains.append(domain)

        for url in urls:

            parsed_url = urlparse(url)

            domain = parsed_url.netloc.lower()

            if domain.startswith("www."):
                domain = domain[4:]

            if domain:
                domains.append(domain)

        return list(dict.fromkeys(domains))


    def contains_pattern(
        self,
        message,
        patterns
    ):

        message_lower = message.lower()

        return any(
            pattern in message_lower
            for pattern in patterns
        )


    def detect_suspicious_attachment(
        self,
        message
    ):

        message_lower = message.lower()

        return any(
            extension in message_lower
            for extension
            in self.SUSPICIOUS_EXTENSIONS
        )


    def collect_suspicious_keywords(
        self,
        message
    ):

        all_patterns = (
            self.CREDENTIAL_PATTERNS
            + self.MONEY_PATTERNS
            + self.URGENCY_PATTERNS
            + self.THREAT_PATTERNS
        )

        message_lower = message.lower()

        found = []

        for pattern in all_patterns:

            if pattern in message_lower:
                found.append(pattern)

        return list(dict.fromkeys(found))


if __name__ == "__main__":

    suspicious_message = """
    From: Microsoft IT Support
    <support@micros0ft-security.com>

    Subject: URGENT - Account Suspension

    Your Microsoft 365 account will be
    suspended today due to unauthorized activity.

    Verify your account immediately:

    https://microsoft-login.example.com

    Enter your username and password to continue.

    Failure to verify your account will result
    in your access being revoked.
    """

    analyzer = MessageAnalyzer()

    indicators = analyzer.analyze(
        suspicious_message
    )

    print("\nExtracted Indicators")
    print("=" * 50)

    print(
        f"Email addresses: "
        f"{indicators.email_addresses}"
    )

    print(
        f"URLs: "
        f"{indicators.urls}"
    )

    print(
        f"Domains: "
        f"{indicators.domains}"
    )

    print(
        f"Credential request: "
        f"{indicators.credential_request}"
    )

    print(
        f"Money request: "
        f"{indicators.money_request}"
    )

    print(
        f"Urgency: "
        f"{indicators.urgency}"
    )

    print(
        f"Threat language: "
        f"{indicators.threat_language}"
    )

    print(
        f"Suspicious attachment: "
        f"{indicators.suspicious_attachment}"
    )

    print(
        f"Suspicious keywords: "
        f"{indicators.suspicious_keywords}"
    )