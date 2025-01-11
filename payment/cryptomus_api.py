from __future__ import annotations

import asyncio
import typing
import uuid
from typing import Literal, Optional

from pyCryptomusAPI import Invoice as CryptomusInvoice
from pyCryptomusAPI import pyCryptomusAPI
from pydantic import PrivateAttr
from decouple import config

from payment.base import BaseMerchant, Currency, InvoiceInfo, MerchantEnum


class Cryptomus(BaseMerchant):
    create_url: Optional[str] = "https://api.cryptomus.com/v1/payment"
    status_url: Optional[str] = "https://api.cryptomus.com/v1/payment/info"

    merchant: Literal[MerchantEnum.CRYPTOMUS] = MerchantEnum.CRYPTOMUS  # type: ignore
    _client: pyCryptomusAPI = PrivateAttr()

    def model_post_init(self, __context: typing.Any) -> None:
        if not self.shop_id:
            raise Exception("shop_id is required for Cryptomus")

        self._client = pyCryptomusAPI(
            self.shop_id,
            self.api_key.get_secret_value(),
        )

    @property
    def client(self) -> pyCryptomusAPI:
        return self._client

    async def create_invoice(
        self,
        user_id: int,
        amount: int | float | str,
        currency: Currency = Currency.RUB,
        description: str | None = None,
    ) -> InvoiceInfo:
        order_id = uuid.uuid4().hex

        invoice: CryptomusInvoice | None = await asyncio.to_thread(
            self.client.create_invoice,
            amount=amount,
            currency=currency,
            order_id=order_id,
        )

        if not invoice:
            raise Exception("Error create invoice")

        if not invoice.order_id:
            raise Exception("Error create invoice. Order_id is None")

        extra_data = {
            "order_id": order_id,
        }

        return InvoiceInfo(
            user_id=user_id,
            amount=float(amount),
            currency=currency,
            invoice_id=invoice.order_id,
            pay_url=invoice.url,
            description=description,
            extra_data=extra_data,
            merchant=self.merchant,
        )

    async def is_paid(self, invoice_id: str) -> bool:
        invoice: CryptomusInvoice = await asyncio.to_thread(  # type: ignore
            self.client.payment_information,
            order_id=invoice_id,
        )
        return bool(invoice.is_final)

cryptomus_client = Cryptomus(
    shop_id=config("MERCHANT_UUID"),
    api_key=config('CRYPTOMUS_API_KEY')
)

def check_payment(order_id):
    payment_info = cryptomus_client._client.payment_information(order_id=order_id)
    return payment_info