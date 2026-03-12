from dataclasses import dataclass


@dataclass(frozen=True)
class AccountCredentials:
    username: str
    password: str
    is_custom: bool = False