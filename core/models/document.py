from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.models import Base


class Document(Base):
    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String, nullable=False)
    transfer_rules = relationship("TransferRule", secondary="transfer_rule_documents",
                                  back_populates="required_documents", lazy="noload")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.name})>"
