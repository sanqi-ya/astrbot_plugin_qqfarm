#!/usr/bin/env python3
"""
QQ Farm Bot UI API 客户端
用于调用 qq-farm-bot-ui 项目的 API，支持 x-admin-token 认证
"""

import requests
import json
from typing import Optional, Dict, Any, List


class QQFarmAPI:
    """QQ Farm Bot UI API 客户端"""
    
    def __init__(
        self,
        base_url: str = "http://103.217.186.84:58130",
        admin_password: str = "sanqi2003.",
        token: str = "15fe58ac2bc1dc7e4be02621ec72540aa802a36689513ea7",
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.admin_password = admin_password
        self.token = token
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["x-admin-token"] = self.token
        return headers
    
    def login(self) -> bool:
        url = f"{self.base_url}/api/login"
        data = {"password": self.admin_password}
        
        try:
            response = self._session.post(url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok") and result.get("data", {}).get("token"):
                    self.token = result["data"]["token"]
                    return True
                else:
                    return False
            else:
                return False
                
        except requests.exceptions.RequestException:
            return False
    
    def get_accounts(self) -> Optional[List[Dict]]:
        url = f"{self.base_url}/api/accounts"
        
        try:
            response = self._session.get(url, headers=self._get_headers(), timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    accounts = result.get("data", {}).get("accounts", result.get("data", []))
                    if isinstance(accounts, dict):
                        return accounts.get("accounts", [])
                    return accounts if isinstance(accounts, list) else []
            else:
                return []
                
        except requests.exceptions.RequestException:
            return []
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        url = f"{self.base_url}/api/accounts/{account_id}"
        headers = self._get_headers()
        headers["x-account-id"] = account_id
        
        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return result.get("data")
            return None
                
        except requests.exceptions.RequestException:
            return None
    
    def update_code(self, account_id: str, code: str) -> bool:
        url = f"{self.base_url}/api/accounts"
        data = {"id": account_id, "code": code}
        
        try:
            response = self._session.post(url, json=data, headers=self._get_headers(), timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
            return False
                
        except requests.exceptions.RequestException:
            return False
    
    def start_account(self, account_id: str) -> bool:
        url = f"{self.base_url}/api/accounts/{account_id}/start"
        
        try:
            response = self._session.post(url, json={}, headers=self._get_headers(), timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
            return False
                
        except requests.exceptions.RequestException:
            return False
    
    def stop_account(self, account_id: str) -> bool:
        url = f"{self.base_url}/api/accounts/{account_id}/stop"
        
        try:
            response = self._session.post(url, json={}, headers=self._get_headers(), timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
            return False
                
        except requests.exceptions.RequestException:
            return False
    
    def get_status(self, account_id: Optional[str] = None) -> Optional[Dict]:
        url = f"{self.base_url}/api/status"
        headers = self._get_headers()
        if account_id:
            headers["x-account-id"] = account_id
        
        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return result.get("data")
            return None
                
        except requests.exceptions.RequestException:
            return None
