"""UA rotation kept consistent with matching Accept-Language / sec-ch-ua headers,
so the header set looks like one real browser instead of a randomized mix.
"""
import random

PROFILES = [
    {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        "sec_ch_ua": '"Chromium";v="127", "Google Chrome";v="127", "Not;A=Brand";v="99"',
        "platform": "Windows",
    },
    {
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        "sec_ch_ua": '"Chromium";v="127", "Google Chrome";v="127", "Not;A=Brand";v="99"',
        "platform": "macOS",
    },
]


def random_profile() -> dict:
    profile = random.choice(PROFILES)
    return {
        "user_agent": profile["user_agent"],
        "headers": {
            "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
            "sec-ch-ua": profile["sec_ch_ua"],
            "sec-ch-ua-platform": f'"{profile["platform"]}"',
        },
    }
