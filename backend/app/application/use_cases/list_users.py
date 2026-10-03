"""The users the demo can switch between."""
from app.application.ports.transaction_repository import TransactionRepository
from app.domain.entities.user import User


class ListUsers:
    def __init__(self, repository: TransactionRepository):
        self._repository = repository

    def execute(self) -> list[User]:
        return self._repository.list_users()
