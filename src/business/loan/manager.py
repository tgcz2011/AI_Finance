from __future__ import annotations

from decimal import Decimal

from src.core.account.manager import AccountManager
from src.core.account.models import Loan
from src.core.constants import (
    DEFAULT_COLLATERAL_LIQUIDATION_RATIO,
    DEFAULT_COLLATERAL_WARNING_RATIO,
    DEFAULT_DAILY_INTEREST_RATE,
    DEFAULT_MAX_LOAN_RATIO,
    ZERO,
    D,
)
from src.core.enums import Currency
from src.core.types.result import Err, Ok, Result


class LoanManager:
    def __init__(self, account_manager: AccountManager) -> None:
        self._account_mgr = account_manager
        self._loans: dict[str, list[Loan]] = {}
        self._daily_rate = DEFAULT_DAILY_INTEREST_RATE
        self._max_loan_ratio = DEFAULT_MAX_LOAN_RATIO
        self._warning_ratio = DEFAULT_COLLATERAL_WARNING_RATIO
        self._liquidation_ratio = DEFAULT_COLLATERAL_LIQUIDATION_RATIO
        self._initial_assets: dict[str, Decimal] = {}

    def set_initial_assets(self, ai_player_id: str, amount: Decimal) -> None:
        self._initial_assets[ai_player_id] = amount

    def check_auto_loan(self, ai_player_id: str, required_cny: Decimal) -> Result[Decimal]:
        cny_balance = self._account_mgr.get_balance(ai_player_id, Currency.CNY)
        if cny_balance >= required_cny:
            return Ok(ZERO)
        shortage = required_cny - cny_balance
        max_loan = self._initial_assets.get(ai_player_id, ZERO) * self._max_loan_ratio
        current_debt = self._get_total_debt(ai_player_id)
        available = max_loan - current_debt
        if available <= ZERO:
            return Err(f"Max loan reached: debt {current_debt} >= max {max_loan}")
        loan_amount = min(shortage, available)
        return self.disburse(ai_player_id, loan_amount)

    def disburse(self, ai_player_id: str, amount: Decimal) -> Result[Decimal]:
        if amount <= ZERO:
            return Err("Loan amount must be positive")
        credit_result = self._account_mgr.credit_cash(ai_player_id, Currency.CNY, amount)
        if credit_result.is_err:
            return Err(credit_result.error)
        loan = Loan(
            account_id=f"{ai_player_id}_CNY",
            principal=amount,
            interest_accrued=ZERO,
            daily_rate=self._daily_rate,
            is_active=True,
        )
        self._loans.setdefault(ai_player_id, []).append(loan)
        return Ok(amount)

    def apply_daily_interest(self, ai_player_id: str) -> Result[Decimal]:
        loans = self._loans.get(ai_player_id, [])
        total_interest = ZERO
        updated = []
        for loan in loans:
            if loan.is_active:
                daily_interest = (loan.principal + loan.interest_accrued) * loan.daily_rate
                total_interest += daily_interest
                updated.append(Loan(
                    account_id=loan.account_id,
                    principal=loan.principal,
                    interest_accrued=loan.interest_accrued + daily_interest.quantize(D("0.00000001")),
                    daily_rate=loan.daily_rate,
                    is_active=True,
                    disbursed_at=loan.disbursed_at,
                ))
            else:
                updated.append(loan)
        self._loans[ai_player_id] = updated
        return Ok(total_interest.quantize(D("0.00000001")))

    def get_collateral_ratio(self, ai_player_id: str, total_assets: Decimal) -> Decimal:
        total_debt = self._get_total_debt(ai_player_id)
        if total_debt <= ZERO:
            return ZERO
        if total_assets <= ZERO:
            return D("Infinity")
        return total_debt / total_assets

    def check_collateral(self, ai_player_id: str, total_assets: Decimal) -> str:
        ratio = self.get_collateral_ratio(ai_player_id, total_assets)
        if ratio > self._liquidation_ratio and ratio != ZERO:
            return "LIQUIDATION"
        if ratio > self._warning_ratio and ratio != ZERO:
            return "WARNING"
        return "OK"

    def repay(self, ai_player_id: str, amount: Decimal) -> Result[Decimal]:
        if amount <= ZERO:
            return Err("Repayment amount must be positive")
        cny_balance = self._account_mgr.get_balance(ai_player_id, Currency.CNY)
        if cny_balance < amount:
            return Err(f"Insufficient CNY for repayment: {cny_balance} < {amount}")
        debit_result = self._account_mgr.debit_cash(ai_player_id, Currency.CNY, amount)
        if debit_result.is_err:
            return Err(debit_result.error)
        remaining = amount
        updated_loans = []
        for loan in self._loans.get(ai_player_id, []):
            if not loan.is_active or remaining <= ZERO:
                updated_loans.append(loan)
                continue
            total_owed = loan.principal + loan.interest_accrued
            if remaining >= total_owed:
                remaining -= total_owed
                updated_loans.append(Loan(
                    account_id=loan.account_id,
                    principal=ZERO,
                    interest_accrued=ZERO,
                    daily_rate=loan.daily_rate,
                    is_active=False,
                    disbursed_at=loan.disbursed_at,
                ))
            else:
                pay_interest = min(remaining, loan.interest_accrued)
                remaining -= pay_interest
                new_interest = loan.interest_accrued - pay_interest
                pay_principal = min(remaining, loan.principal)
                remaining -= pay_principal
                new_principal = loan.principal - pay_principal
                updated_loans.append(Loan(
                    account_id=loan.account_id,
                    principal=new_principal,
                    interest_accrued=new_interest,
                    daily_rate=loan.daily_rate,
                    is_active=new_principal > ZERO,
                    disbursed_at=loan.disbursed_at,
                ))
        self._loans[ai_player_id] = updated_loans
        return Ok(amount - remaining)

    def _get_total_debt(self, ai_player_id: str) -> Decimal:
        loans = self._loans.get(ai_player_id, [])
        return sum((ln.principal + ln.interest_accrued) for ln in loans if ln.is_active)

    def get_total_debt(self, ai_player_id: str) -> Decimal:
        return self._get_total_debt(ai_player_id)

    def get_active_loans(self, ai_player_id: str) -> list[Loan]:
        return [ln for ln in self._loans.get(ai_player_id, []) if ln.is_active]
