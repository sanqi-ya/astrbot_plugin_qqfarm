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
        self._client: Optional[httpx.AsyncClient] = None

    async def ainit(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["x-admin-token"] = self.token
        return headers

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if self._client is None:
            await self.ainit()
        assert self._client is not None

        url = f"{self.base_url}{path}"
        try:
            response = await self._client.request(
                method,
                url,
                headers=headers or self._get_headers(),
                json=json_data,
            )
        except httpx.RequestError:
            return None

        if response.status_code != 200:
            return None

        try:
            return response.json()
        except ValueError:
            return None

    async def login(self) -> bool:
        result = await self._request("POST", "/api/login", json_data={"password": self.admin_password})
        if not result:
            return False
        if result.get("ok") and result.get("data", {}).get("token"):
            self.token = result["data"]["token"]
            return True
        return False

    async def get_accounts(self) -> Optional[List[Dict[str, Any]]]:
        result = await self._request("GET", "/api/accounts")
        if not result or not result.get("ok"):
            return []

        data = result.get("data", {})
        if isinstance(data, dict):
            accounts = data.get("accounts", [])
        else:
            accounts = []

        if isinstance(accounts, dict):
            return accounts.get("accounts", [])
        if isinstance(accounts, list):
            return accounts
        return []

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        headers = self._get_headers()
        headers["x-account-id"] = account_id

        result = await self._request("GET", f"/api/accounts/{account_id}", headers=headers)
        if not result or not result.get("ok"):
            return None
        return result.get("data")

    async def update_code(self, account_id: str, code: str) -> bool:
        result = await self._request("POST", "/api/accounts", json_data={"id": account_id, "code": code})
        return bool(result and result.get("ok"))

    async def start_account(self, account_id: str) -> bool:
        result = await self._request("POST", f"/api/accounts/{account_id}/start", json_data={})
        return bool(result and result.get("ok"))

    async def stop_account(self, account_id: str) -> bool:
        result = await self._request("POST", f"/api/accounts/{account_id}/stop", json_data={})
        return bool(result and result.get("ok"))

    async def get_status(self, account_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        headers = self._get_headers()
        if account_id:
            headers["x-account-id"] = account_id

        result = await self._request("GET", "/api/status", headers=headers)
        if not result or not result.get("ok"):
            return None
        return result.get("data")