from enum import StrEnum

class TaskStatus(StrEnum):
    PENDING = "pending"
    DRAFT_READY = "draft_ready"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    REJECTED = "rejected"
    FAILED = "failed"




ALLOWED_TRANSITIONS = {
    TaskStatus.PENDING:{
        TaskStatus.DRAFT_READY,
        TaskStatus.REJECTED },
    TaskStatus.DRAFT_READY:{
        TaskStatus.APPROVED,
        TaskStatus.REJECTED
    },
    TaskStatus.APPROVED:{
        TaskStatus.SCHEDULED,
        TaskStatus.REJECTED
    },
    TaskStatus.SCHEDULED:{
        TaskStatus.SENDING,
        TaskStatus.REJECTED
    },
    TaskStatus.SENDING:{
        TaskStatus.SENT,
        TaskStatus.FAILED
    },
    TaskStatus.FAILED:{
        TaskStatus.SCHEDULED,
    },
    TaskStatus.SENT:set(),
    TaskStatus.REJECTED:set(),

}

def can_transition(current: TaskStatus,target: TaskStatus)->bool:
    return target  in ALLOWED_TRANSITIONS[current]


def require_transition(current: TaskStatus, target: TaskStatus)->None:
    if current not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Invalid status transition: {current} -> {target}")