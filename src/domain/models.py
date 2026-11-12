from datetime import datetime, timezone
from enum import  StrEnum
from sqlalchemy import DateTime, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass



class TaskStatus(StrEnum):
    PENDING = "pending"
    DRAFT_READY = "draft_ready"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    REJECTED = "rejected"

class SendResult(StrEnum):
    SENT = "sent"
    FAILED = "failed"
    UNKNOWN = "unknown"


def utc_now():
    return datetime.now(timezone.utc)

class Task(Base):
    __tablename__ = "tasks"
    id:Mapped[int]=mapped_column(primary_key=True)
    reminder_text:Mapped[str]=mapped_column(Text,nullable=False)
    title:Mapped[str]=mapped_column(String(200),nullable=False)
    recipient_email:Mapped[str|None]=mapped_column(String(320))
    status: Mapped[TaskStatus] = mapped_column(
        String(30),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

class EmailDraft(Base):
    __tablename__ = "email_drafts"
    id:Mapped[int]=mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"),
        nullable=False,
        index=True,
    )
    subject:Mapped[str]=mapped_column(String(200),nullable=False)
    body:Mapped[str]=mapped_column(Text,nullable=False)
    approved_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True))
    send_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True))
    task: Mapped["Task"] = relationship(back_populates="email_drafts")


class SendLog(Base):
    __tablename__ = "send_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    email_draft_id: Mapped[int] = mapped_column(
        ForeignKey("email_drafts.id"),
        nullable=False,
        index=True,
    )

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    result: Mapped[SendResult] = mapped_column(
        String(20),
        nullable=False,
    )

    gmail_message_id: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)
    email_draft: Mapped["EmailDraft"] = relationship(
        back_populates="send_logs"
    )


