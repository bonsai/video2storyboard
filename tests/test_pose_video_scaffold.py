from video2storyboard.pose_video import rainbow_bgr


def test_rainbow_bgr_returns_valid_channels():
    color = rainbow_bgr(2, 7)
    assert len(color) == 3
    assert all(0 <= channel <= 255 for channel in color)
