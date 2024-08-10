from datetime import timedelta

from pydantic import BaseModel


class TimeDeltaInfo(BaseModel):
    days: int
    hours: int
    minutes: int

    def to_timedelta(self) -> timedelta:
        return timedelta(days=self.days, hours=self.hours, minutes=self.minutes)
