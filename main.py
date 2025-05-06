import os
import time
from typing import Union
import curl_cffi.requests
import tempfile 
import subprocess
from utils.encryption import create_wb_result
import structlog

logger = structlog.get_logger()

class CfSolver:
    def __init__(self) -> None: # i bet no one knows init returns none!!!!
        self.session = curl_cffi.requests.Session(impersonate="chrome133a")
        self.session.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.8',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }
        #  proxy = random.choice(open("proxies.txt","r")).strip()
        #  self.session.proxies = {'http': 'http://' + proxy.strip(), 'https': 'http://' + proxy.strip()}

    def get_solution(self, challenge_url: str) -> Union[bool, str]:
        challenge_website = challenge_url.split('/cdn-cgi/')[0]
        cloudflare_result = self.session.get(challenge_url)
        cf_ray_id = cloudflare_result.headers["cf-ray"]
        if "-" in cf_ray_id:
            cf_ray_id, _country = cf_ray_id.split("-")
        cloudflare_result = cloudflare_result.content

        temp_js = tempfile.NamedTemporaryFile(suffix='.js', delete=False).name
        temp_js_2 = tempfile.NamedTemporaryFile(suffix='.js', delete=False).name

        try:
            with open(temp_js, "wb") as f:
                f.write(cloudflare_result)

            subprocess.run(f"obfuscator-io-deobfuscator {temp_js} -o {temp_js_2}", shell=True, capture_output=True, text=True)
            
            with open(temp_js_2, "r") as f:
                deobfuscated_result = f.read()

            cloudflare_enc_key = deobfuscated_result.split('".charAt(')[0].split('"')[-1]
            challenge_url = f"{challenge_website}/cdn-cgi/challenge-platform/h/b/jsd/r/" + deobfuscated_result.split('/jsd/r/')[1].split('"')[0] + cf_ray_id
            wb_result = create_wb_result(self.session.headers["user-agent"], cloudflare_enc_key, challenge_website)

            logger.info("Solving cloudflare challenge.", challenge_url=challenge_url[:50] + "...", encoded_payload=wb_result[:30] + "..")

            self.session.headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.5',
                'cache-control': 'no-cache',
                'content-type': 'text/plain;charset=UTF-8',
                'origin': challenge_website,
                'pragma': 'no-cache',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            }
            response = self.session.post(challenge_url, data=wb_result)
            
            if response.status_code == 200:
                logger.info("Cloudflare challenge successfully solved.", cf_clearance=self.session.cookies["cf_clearance"][:50]+"..")
                return self.session.cookies["cf_clearance"]
            else:
                logger.error("Error happened while solving cloudflare.")
                return False
        finally:
            if os.path.exists(temp_js):
                os.unlink(temp_js)
            if os.path.exists(temp_js_2):
                os.unlink(temp_js_2)




solver = CfSolver()
solver.get_solution("https://discord.com/cdn-cgi/challenge-platform/scripts/jsd/main.js")