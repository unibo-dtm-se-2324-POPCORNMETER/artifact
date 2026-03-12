from __future__ import annotations

from dataclasses import dataclass

from popcorn_meter.domain.value_objects.email import Email


@dataclass(frozen=True)
class UserRegistration:
    username: str
    email: str
    password: str


class UserFactory:
    @staticmethod
    def create_registration(username: str, email: str, password: str) -> UserRegistration:
        cleaned_username = username.strip()
        cleaned_password = password
        normalized_email = str(Email(email))

        if not cleaned_username:
            raise ValueError("Username cannot be empty")
        if not cleaned_password:
            raise ValueError("Password cannot be empty")

        return UserRegistration(
            username=cleaned_username,
            email=normalized_email,
            password=cleaned_password,
        )

    @staticmethod
    def normalize_login_email(email: str) -> str:
        return str(Email(email))
