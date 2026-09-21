def has_conflicts(meetings: list[tuple[int, int]]) -> bool:
    if not meetings or len(meetings) == 1:
        return False
    sorted_meetings = sorted(meetings, key=lambda x: x[0])
    for i in range(len(sorted_meetings) - 1):
        current_meeting = sorted_meetings[i]
        next_meeting = sorted_meetings[i + 1]
        if current_meeting[1] > next_meeting[0]:
            return True
    return False
