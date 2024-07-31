from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from core.models import Base


class TransferProvider(Base):
    name: Mapped[str] = mapped_column(String, nullable=False)

    # TODO: think where it should be stored, I mean the link to the provider's source
    # url: Mapped[str] = mapped_column(String, nullable=False)
    # api_key: Mapped[str] = mapped_column(String, nullable=True) # TODO: think about it too, if we need it here or not

    # TODO: Idea how to make it easy switchable (turn on/off the provider)
    # is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return "<TransferProviders(id=%s, name=%s)>" % (self.id, self.name)
