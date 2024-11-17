import asyncio
import requests
import logging


logger = logging.getLogger(__name__)


class ServiceManager:
    def __init__(self, base_url: str, token: str, method:str):
        self.base_url = base_url
        self.headers = {
            'accept': 'application/json',
            'Bearer': token
        }
        # dynamically set request method
        self.request_method = getattr(requests, method.lower())

    async def async_request(self, data=None):
        try:
            res = await asyncio.to_thread(self.request_method, self.base_url, headers=self.headers, json=data)
            return res
        except Exception as e:
            logger.warning('Request not successful.')

    def request(self, data=None):
        res = self.request_method(self.base_url, headers=self.headers, json=data)
        return res
