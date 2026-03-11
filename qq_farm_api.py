#!/usr/bin/env python3
"""
QQ Farm Bot UI API client (async)
"""

from typing import Optional, Dict, Any, List

import httpx


class QQFarmAPI:
    """QQ Farm Bot UI API client"""

    def __init__(
        self,
        base_url: str,
        admin_password: str = "",
        token: str = "",
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.admin_password = admin_password
        self.token = token
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["x-admin-token"] = self.token
        return headers

    async def close(self) -> None:
        await self._client.aclose()

    async def login(self) -> bool:
        url = f"{self.base_url}/api/login"
        data = {"password": self.admin_password}

        try:
            response = await self._client.post(url, json=data, timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok") and result.get("data", {}).get("token"):
                    self.token = result["data"]["token"]
                    return True
            return False
        except httpx.RequestError:
            return False

    async def get_accounts(self) -> Optional[List[Dict[str, Any]]]:
        url = f"{self.base_url}/api/accounts"

        try:
            response = await self._client.get(url, headers=self._get_headers(), timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    accounts = result.get("data", {}).get("accounts", result.get("data", []))
                    if isinstance(accounts, dict):
                        return accounts.get("accounts", [])
                    return accounts if isinstance(accounts, list) else []
            return []
        except httpx.RequestError:
            return []

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/api/accounts/{account_id}"
        headers = self._get_headers()
        headers["x-account-id"] = account_id

        try:
            response = await self._client.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return result.get("data")
            return None
        except httpx.RequestError:
            return None

    async def update_code(self, account_id: str, code: str) -> bool:
        url = f"{self.base_url}/api/accounts"
        data = {"id": account_id, "code": code}

        try:
            response = await self._client.post(url, json=data, headers=self._get_headers(), timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
            return False
        except httpx.RequestError:
            return False

    async def start_account(self, account_id: str) -> bool:
        url = f"{self.base_url}/api/accounts/{account_id}/start"

        try:
            response = await self._client.post(url, json={}, headers=self._get_headers(), timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
            return False
        except httpx.RequestError:
            return False

    async def stop_account(self, account_id: str) -> bool:
        url = f"{self.base_url}/api/accounts/{account_id}/stop"

        try:
            response = await self._client.post(url, json={}, headers=self._get_headers(), timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
            return False
        except httpx.RequestError:
            return False

    async def get_status(self, account_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/api/status"
        headers = self._get_headers()
        if account_id:
            headers["x-account-id"] = account_id

        try:
            response = await self._client.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return result.get("data")
            return None
        except httpx.RequestError:
            return None
