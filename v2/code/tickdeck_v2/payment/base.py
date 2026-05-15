"""base.py — 결제 어댑터 추상 인터페이스 (T07).

feature_spec.md 14.1 정합. 1회 결제·환불 2 메서드만 의무. 정기 결제·할부 X (1단계 MVP 영역 X).

하위 어댑터 (`toss.py`·`stripe.py`) = 본 abstract class 상속·`charge_once`·`refund` 구현 강제.
실 구현 X·인터페이스만. T08 (toss·sandbox 결재 영역)·T09 (stripe placeholder) = 별도 task.

사용:
    from tickdeck_v2.payment import PaymentAdapter, ChargeResult

    class MyAdapter(PaymentAdapter):
        def charge_once(self, amount, currency, metadata):
            ...
        def refund(self, charge_id):
            ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ChargeResult:
    """1회 결제 결과. 성공·실패 둘 다 본 dataclass."""

    success: bool
    charge_id: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RefundResult:
    """환불 결과. 성공·실패 둘 다 본 dataclass."""

    success: bool
    refund_id: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Mapping[str, Any] = field(default_factory=dict)


class PaymentAdapter(ABC):
    """결제 어댑터 abstract base.

    하위 어댑터 = 1 결제 PG 1 어댑터. `charge_once`·`refund` 2 메서드 구현 강제.
    정기 결제·할부·부분 환불 = 1단계 X (2단계 영역 추가 메서드 검토).
    """

    @abstractmethod
    def charge_once(
        self,
        amount: int,
        currency: str,
        metadata: Mapping[str, Any],
    ) -> ChargeResult:
        """1회 결제 호출.

        Args:
            amount: 결제 금액 (정수 단위 — KRW 원·USD 센트).
            currency: ISO 4217 통화 코드 (예: "KRW"·"USD").
            metadata: 주문 식별·구매자 정보 영역 (PG별 strict 필드 자기 처리).

        Returns:
            ChargeResult — 성공 시 `charge_id` 필수·실패 시 `error_message` 필수.

        Raises:
            구현 어댑터 = 가능하면 예외 X·`ChargeResult(success=False, ...)` 반환.
            네트워크·타임아웃 등 외부 예외만 raise OK.
        """

    @abstractmethod
    def refund(self, charge_id: str) -> RefundResult:
        """환불 호출 (전액).

        Args:
            charge_id: `charge_once` 영역에서 받은 결제 식별자.

        Returns:
            RefundResult — 성공 시 `refund_id` 필수·실패 시 `error_message` 필수.

        Raises:
            구현 어댑터 = 가능하면 예외 X·`RefundResult(success=False, ...)` 반환.
        """
