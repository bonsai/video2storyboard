from types import SimpleNamespace

from video2storyboard.pose_tasks import landmarks_to_records, pose_connections


def test_tasks_landmarks_keep_legacy_record_fields():
    landmarks = [
        SimpleNamespace(x=0.1, y=0.2, z=-0.3, visibility=0.9, presence=0.8),
        SimpleNamespace(x=0.4, y=0.5, z=0.6, visibility=0.7, presence=0.65),
    ]

    records = landmarks_to_records(landmarks)

    assert records[0] == {
        "index": 0,
        "name": "NOSE",
        "x": 0.1,
        "y": 0.2,
        "z": -0.3,
        "visibility": 0.9,
        "presence": 0.8,
    }
    assert records[1]["name"] == "LEFT_EYE_INNER"
    assert records[1]["index"] == 1
    assert records[1]["presence"] == 0.65


def test_pose_connections_are_plain_integer_pairs():
    connections = pose_connections()

    assert connections
    assert all(
        isinstance(start, int) and isinstance(end, int)
        for start, end in connections
    )
