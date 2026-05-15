"""payment/ — 결제 어댑터 영역.

`PaymentAdapter` abstract class·`ChargeResult`·`RefundResult` 정의.
1단계 MVP = waitlist만·실 결제 X·placeholder. 2단계 = toss·stripe 활성화.

T07 = 인터페이스만. T08 (toss·결재 영역)·T09 (stripe placeholder) = 별도 task.
"""

from tickdeck_v2.payment.base import (
    ChargeResult,
    PaymentAdapter,
    RefundResult,
)

__all__ = ["PaymentAdapter", "ChargeResult", "RefundResult"]
