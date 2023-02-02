# -*- coding: utf-8 -*-

from datetime import date
from uuid import uuid4
from dataclasses import dataclass, field


def mk_ref() -> str:
    return uuid4().hex[:24]


@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int
    order_id: str = field(default_factory=mk_ref)


class Batch:
    def __init__(self, sku: str, quantity: int, eta: date | None = None) -> None:
        self.batchid: str = mk_ref()
        self.sku: str = sku
        self.eta: date | None = eta
        self._purchased_quantity: int = quantity
        self._allocations: set[OrderLine] = set()

    @property
    def quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    @property
    def allocated_quantity(self) -> int:
        return sum(ord.quantity for ord in self._allocations)

    def can_allocate(self, order_line: OrderLine) -> bool:
        return (order_line.sku == self.sku
                and self.quantity >= order_line.quantity)

    def allocate(self, order_line: OrderLine) -> None:
        if self.can_allocate(order_line):
            self._allocations.add(order_line)

    def deallocate(self, order_line: OrderLine) -> None:
        if order_line in self._allocations:
            self._allocations.remove(order_line)

def make_batch_and_line() -> tuple[Batch, OrderLine]:
    return (
        Batch(sku='RED-CHAIR', quantity=20),
        OrderLine(sku='RED-CHAIR', quantity=2)
    )

def test_can_allocate_order_with_available_quantity_greater_than_order_line_quantity() -> None:
    batch, order_line = make_batch_and_line()
    assert batch.can_allocate(order_line)


def test_allocate_order_lines_reduces_batch_quantity_by_order_line_quantity() -> None:
    batch, order_line = make_batch_and_line()
    batch.allocate(order_line)
    assert batch.quantity == 18


def test_cannot_allocate_order_lines_quantity_greater_than_batch_size() -> None:
    batch = Batch(sku='BLUE-CUSHION', quantity=1)
    order_line = OrderLine(sku='BLUE-CUSHION', quantity=2)
    assert batch.can_allocate(order_line) is False


def test_cannot_allocate_different_sku() -> None:
    batch = Batch(sku='BLUE-CUSHION', quantity=10)
    order_line = OrderLine(sku='BLUE-VASE', quantity=2)
    assert batch.can_allocate(order_line) is False


def test_allocation_is_idempotent() -> None:
    batch = Batch(sku='BLUE-VASE', quantity=10)
    order_line = OrderLine(sku='BLUE-VASE', quantity=2)
    batch.allocate(order_line)
    batch.allocate(order_line)
    assert batch.quantity == 8


def test_can_only_deallocate_allocated_order():
    batch, order_line = make_batch_and_line()
    start_qty = batch.quantity
    batch.deallocate(order_line)
    assert batch.quantity == start_qty
