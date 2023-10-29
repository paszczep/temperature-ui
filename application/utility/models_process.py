from dataclasses import dataclass


@dataclass
class ExecuteTaskRead:
    __tablename__ = "task_reads",
    task_id: str
    read_id: str


@dataclass
class ExecuteCheck:
    __tablename__ = 'container_check'
    id: str
    container: str
    timestamp: int
    logged: str
    received: str
    power: str
    read_setpoint: str


@dataclass
class ExecuteSet:
    __tablename__ = 'temp_set'
    id: str
    status: str
    temperature: int
    timestamp: int
    container: str


@dataclass
class ExecuteTask:
    __tablename__ = 'task'
    id: str
    start: int
    duration: int
    t_start: int
    t_min: int
    t_max: int
    t_freeze: int
    status: str
    container: str
    reads: list
    controls: list


@dataclass(frozen=True)
class ExecuteSetControl:
    __tablename__ = "set_controls"
    set_id: str
    control_id: str


@dataclass(frozen=True)
class ExecuteTaskControl:
    __tablename__ = "task_controls"
    task_id: str
    control_id: str


def task_from_dict(t: dict) -> ExecuteTask:
    return ExecuteTask(
        id=t['id'],
        start=t['start'],
        duration=t['duration'],
        t_start=t['t_start'],
        t_min=t['t_min'],
        t_max=t['t_max'],
        t_freeze=t['t_freeze'],
        status=t['status'],
        container='',
        reads=list(),
        controls=list()
    )


