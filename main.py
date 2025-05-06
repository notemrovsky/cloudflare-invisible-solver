import random
import subprocess
import tempfile
from typing import List, Optional, Union

import structlog
from curl_cffi import requests

from utils.fingerprint import create_wb_result
from utils import constants

logger = structlog.get_logger()


class CfSolver:
    def __init__(self, proxies: Optional[List[str]] = None) -> None:
        self.proxies = proxies

    def _create_session(self) -> requests.Session:
        session = requests.Session(
            impersonate="chrome133a", headers=constants.DEFAULT_HEADERS.copy()
        )
        if self.proxies:
            proxy = "http://" + random.choice(self.proxies)
            session.proxies = {"http": proxy, "https": proxy}
        return session

    def get_solution(self, challenge_url: str) -> Union[bool, str]:
        session = self._create_session()

        challenge_website = challenge_url.split("/cdn-cgi/")[0]
        cloudflare_result = session.get(challenge_url)
        cf_ray_id = cloudflare_result.headers["cf-ray"]

        cf_ray_id = cf_ray_id.split("-")[0]

        cloudflare_result = cloudflare_result.content

        with tempfile.NamedTemporaryFile(
            suffix=".js", delete=False
        ) as temp_js_file, tempfile.NamedTemporaryFile(
            suffix=".js", delete=False
        ) as temp_js_2_file:
            temp_js = temp_js_file.name
            temp_js_2 = temp_js_2_file.name

            with open(temp_js, "wb") as f:
                f.write(cloudflare_result)

            subprocess.run(
                f"obfuscator-io-deobfuscator {temp_js} -o {temp_js_2}",
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )

            with open(temp_js_2, "r", encoding="utf-8") as f:
                deobfuscated_result = f.read()

            cloudflare_enc_key = deobfuscated_result.split('".charAt(')[0].split('"')[
                -1
            ]
            challenge_url = (
                f"{challenge_website}/cdn-cgi/challenge-platform/h/b/jsd/r/"
                + deobfuscated_result.split("/jsd/r/")[1].split('"')[0]
                + cf_ray_id
            )

            wb_result = create_wb_result(
                session.headers["user-agent"],
                cloudflare_enc_key,
                challenge_website
            )

            logger.info(
                "Solving cloudflare challenge.",
                challenge_url=challenge_url[:50] + "...",
                encoded_payload=wb_result[:30] + "..",
            )

            session.headers = constants.CHALLENGE_HEADERS.copy()
            session.headers["origin"] = challenge_website
            response = session.post(challenge_url, data=wb_result)

            if response.status_code == 200:
                logger.info(
                    "Cloudflare challenge successfully solved.",
                    cf_clearance=session.cookies["cf_clearance"][:50] + "..",
                )
                return session.cookies["cf_clearance"]
            logger.error("Error happened while solving cloudflare.")
            return False


if __name__ == "__main__":
    solver = CfSolver()
    solver.get_solution(
        "https://discord.com/cdn-cgi/challenge-platform/scripts/jsd/main.js"
    )
