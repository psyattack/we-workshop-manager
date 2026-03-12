import base64
import sys

from domain.models.account import AccountCredentials


class AccountService:
    _DEFAULT_ACCOUNTS = {
        "ruiiixx": "UzY3R0JUQjgzRDNZ",
        "premexilmenledgconis": "M3BYYkhaSmxEYg==",
        "vAbuDy": "Qm9vbHE4dmlw",
        "adgjl1182": "UUVUVU85OTk5OQ==",
        "gobjj16182": "enVvYmlhbzgyMjI=",
        "787109690": "SHVjVXhZTVFpZzE1",
        "weworkshopmanager2": "a2Fpem9rdV9vX2h5b3U=",
    }

    def __init__(
        self,
        accounts: list[AccountCredentials],
    ):
        self._accounts = accounts

    @classmethod
    def from_runtime_arguments(cls) -> "AccountService":
        custom_login = None
        custom_password = None

        if "-login" in sys.argv:
            try:
                index = sys.argv.index("-login")
                if index + 1 < len(sys.argv):
                    custom_login = sys.argv[index + 1]
            except Exception:
                custom_login = None

        if "-password" in sys.argv:
            try:
                index = sys.argv.index("-password")
                if index + 1 < len(sys.argv):
                    custom_password = sys.argv[index + 1]
            except Exception:
                custom_password = None

        accounts = cls._build_default_accounts()

        if custom_login and custom_password:
            accounts = [
                account
                for account in accounts
                if account.username != "weworkshopmanager2"
            ]
            accounts.append(
                AccountCredentials(
                    username=custom_login,
                    password=custom_password,
                    is_custom=True,
                )
            )

        return cls(accounts)

    @classmethod
    def _build_default_accounts(cls) -> list[AccountCredentials]:
        result: list[AccountCredentials] = []
        for username, encoded_password in cls._DEFAULT_ACCOUNTS.items():
            decoded_password = base64.b64decode(encoded_password).decode("utf-8")
            result.append(
                AccountCredentials(
                    username=username,
                    password=decoded_password,
                    is_custom=False,
                )
            )
        return result

    def get_accounts(self) -> list[str]:
        return [account.username for account in self._accounts]

    def get_account(self, index: int) -> str:
        if not self._accounts:
            return ""

        if 0 <= index < len(self._accounts):
            return self._accounts[index].username

        return self._accounts[0].username

    def get_password(self, account_name: str) -> str:
        for account in self._accounts:
            if account.username == account_name:
                return account.password
        return ""

    def get_credentials(self, index: int) -> tuple[str, str]:
        if not self._accounts:
            return "", ""

        if 0 <= index < len(self._accounts):
            account = self._accounts[index]
        else:
            account = self._accounts[0]

        return account.username, account.password

    def get_credentials_model(self, index: int) -> AccountCredentials:
        if not self._accounts:
            return AccountCredentials(username="", password="")

        if 0 <= index < len(self._accounts):
            return self._accounts[index]

        return self._accounts[0]