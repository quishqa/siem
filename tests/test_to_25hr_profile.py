from siem.cmaq import to_25hr_profile
import numpy as np


def test_to_25hr_profile() -> None:
    profile = np.random.normal(1, 0.5, size=24)
    new_profile = to_25hr_profile(profile)

    assert len(new_profile) == 25
    assert new_profile[0] == new_profile[-1]
