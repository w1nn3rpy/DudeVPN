from __future__ import annotations

import abc
import datetime
import typing
from abc import ABC
from enum import StrEnum
from typing import Any, Literal, Optional, Union

import zoneinfo
from aiohttp import ClientSession
from pydantic import BaseModel, Field, SecretStr, field_serializer

PAYMENT_LIFETIME = 60 * 60  # seconds
TIME_ZONE = zoneinfo.ZoneInfo("Europe/Moscow")


# Alias for Amount
Amount: typing.TypeAlias = float | int | str


class InvoiceStatus(StrEnum):
    """Invoice status."""

    PENDING = "pending"
    SUCCESS = "success"
    EXPIRED = "expired"
    FAIL = "fail"


class InvoiceInfo(BaseModel):
    invoice_id: str
    merchant: MerchantEnum

    user_id: int
    amount: float
    currency: str = "RUB"
    status: InvoiceStatus = InvoiceStatus.PENDING
    pay_url: str | None = None
    description: str | None = None
    extra_data: dict
    expire_at: datetime.datetime = Field(
        default_factory=(
            lambda: datetime.datetime.now(TIME_ZONE)
            + datetime.timedelta(seconds=PAYMENT_LIFETIME)
        )
    )


class Currency(StrEnum):
    """Currency codes."""

    USD = "USD"
    RUB = "RUB"
    EUR = "EUR"
    GBP = "GBP"

    USDT = "USDT"
    BTC = "BTC"
    TON = "TON"
    ETH = "ETH"
    USDC = "USDC"
    BUSD = "BUSD"


class MerchantEnum(StrEnum):
    NONE = "none"
    CRYPTO_CLOUD = "crypto_cloud"
    USDT = "usdt"
    QIWI = "qiwi"
    YOOMONEY = "yoomoney"
    YOOKASSA = "yookassa"
    CRYPTO_PAY = "crypto_pay"
    CRYPTOMUS = "cryptomus"
    WALLET_PAY = "wallet_pay"
    STRIPE = "stripe"
    TRIBUTE = "tribute"
    BETA_TRANSFER_PAY = "beta_transfer_pay"
    PAYOK = "payok"
    AAIO = "aaio"


MerchantUnion = Union[
    Literal[MerchantEnum.NONE],
    Literal[MerchantEnum.CRYPTO_CLOUD],
    Literal[MerchantEnum.USDT],
    Literal[MerchantEnum.QIWI],
    Literal[MerchantEnum.YOOMONEY],
    Literal[MerchantEnum.YOOKASSA],
    Literal[MerchantEnum.CRYPTO_PAY],
    Literal[MerchantEnum.CRYPTOMUS],
    Literal[MerchantEnum.WALLET_PAY],
    Literal[MerchantEnum.STRIPE],
    Literal[MerchantEnum.TRIBUTE],
    Literal[MerchantEnum.BETA_TRANSFER_PAY],
    Literal[MerchantEnum.PAYOK],
    Literal[MerchantEnum.AAIO],
]


class BaseMerchant(BaseModel, ABC):
    shop_id: Optional[str] = None
    api_key: SecretStr
    create_url: Optional[str] = None
    status_url: Optional[str] = None
    session: Optional[ClientSession] = None
    merchant: Literal[MerchantEnum.NONE]

    class Config:
        arbitrary_types_allowed = True

    @property
    def headers(self) -> dict:
        return {}

    @field_serializer("session")
    def serialize_session(self, v: ClientSession) -> None:
        pass

    @field_serializer("api_key")
    def serialize_api_key(self, v: SecretStr) -> str:
        return v.get_secret_value()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = ClientSession(headers=self.headers)
        return self.session

    async def close_session(self):
        if self.session is not None:
            await self.session.close()

    async def make_request(self, method: str, url: str, **kwargs) -> Any:
        session = await self.get_session()
        async with session.request(method, url, **kwargs) as res:
            return await res.json()

    @abc.abstractmethod
    async def create_invoice(
        self,
        user_id: int,
        amount: Amount,
        currency: Currency = Currency.RUB,
        description: str | None = None,
    ) -> InvoiceInfo:
        pass

    @abc.abstractmethod
    async def is_paid(self, invoice_id: str) -> bool:
        pass