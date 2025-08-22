"""
Security Service for threat detection and security monitoring.
"""
import re
import hashlib
import ipaddress
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from collections import defaultdict, Counter
from enum import Enum

from app.shared.infrastructure.container import injectable
from app.shared.infrastructure.cache import cache_service, cached
# User model is now handled by auth-service microservice
# TODO: Replace User model usage with auth service API calls


class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events."""
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SUSPICIOUS_LOGIN = "suspicious_login"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    MALICIOUS_IP = "malicious_ip"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SESSION_HIJACKING = "session_hijacking"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"


@injectable()
class SecurityService:
    """Service for security monitoring and threat detection."""
    
    def __init__(self, db: Session):
        self.db = db
        self.threat_indicators = self._load_threat_indicators()
    
    def _load_threat_indicators(self) -> Dict[str, Set[str]]:
        """Load threat indicators (IPs, patterns, etc.)."""
        return {
            "malicious_ips": {
                # Example malicious IPs (in real implementation, load from threat feeds)
                "192.168.1.100",  # Example
                "10.0.0.1",       # Example
            },
            "suspicious_user_agents": {
                "sqlmap",
                "nikto",
                "nmap",
                "masscan",
                "curl/7.0",  # Very old curl versions
            },
            "malicious_patterns": {
                r"(?i)(union|select|insert|delete|drop|create|alter)\s+",  # SQL injection
                r"(?i)<script[^>]*>.*?</script>",  # XSS
                r"(?i)javascript:",  # JavaScript injection
                r"(?i)eval\s*\(",  # Code injection
            }
        }
    
    async def analyze_login_attempt(
        self,
        username: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze login attempt for security threats."""
        if not timestamp:
            timestamp = datetime.now(timezone.utc)
        
        threats = []
        threat_level = ThreatLevel.LOW
        
        # Check for malicious IP
        if ip_address in self.threat_indicators["malicious_ips"]:
            threats.append({
                "type": SecurityEventType.MALICIOUS_IP.value,
                "description": f"Login attempt from known malicious IP: {ip_address}",
                "severity": ThreatLevel.HIGH.value
            })
            threat_level = ThreatLevel.HIGH
        
        # Check for suspicious user agent
        for suspicious_ua in self.threat_indicators["suspicious_user_agents"]:
            if suspicious_ua.lower() in user_agent.lower():
                threats.append({
                    "type": SecurityEventType.SUSPICIOUS_LOGIN.value,
                    "description": f"Suspicious user agent detected: {user_agent}",
                    "severity": ThreatLevel.MEDIUM.value
                })
                if threat_level == ThreatLevel.LOW:
                    threat_level = ThreatLevel.MEDIUM
        
        # Check for brute force attempts
        brute_force_check = await self._check_brute_force(ip_address, username, success, timestamp)
        if brute_force_check["is_brute_force"]:
            threats.append({
                "type": SecurityEventType.BRUTE_FORCE_ATTEMPT.value,
                "description": f"Brute force attack detected from {ip_address}",
                "severity": ThreatLevel.HIGH.value,
                "details": brute_force_check
            })
            threat_level = ThreatLevel.HIGH
        
        # Check for credential stuffing
        credential_stuffing_check = await self._check_credential_stuffing(ip_address, timestamp)
        if credential_stuffing_check["is_credential_stuffing"]:
            threats.append({
                "type": SecurityEventType.CREDENTIAL_STUFFING.value,
                "description": f"Credential stuffing attack detected from {ip_address}",
                "severity": ThreatLevel.HIGH.value,
                "details": credential_stuffing_check
            })
            threat_level = ThreatLevel.HIGH
        
        # Store login attempt for analysis
        await self._store_login_attempt(username, ip_address, user_agent, success, timestamp)
        
        return {
            "threat_detected": len(threats) > 0,
            "threat_level": threat_level.value,
            "threats": threats,
            "ip_address": ip_address,
            "username": username,
            "timestamp": timestamp.isoformat(),
            "recommendations": self._get_security_recommendations(threats)
        }
    
    async def _check_brute_force(
        self,
        ip_address: str,
        username: str,
        success: bool,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Check for brute force attacks."""
        # Get recent failed attempts from this IP
        recent_attempts_key = f"login_attempts:{ip_address}"
        recent_attempts = await cache_service.get(recent_attempts_key) or []
        
        # Count failed attempts in last 15 minutes
        cutoff_time = timestamp - timedelta(minutes=15)
        recent_failures = [
            attempt for attempt in recent_attempts
            if not attempt["success"] and 
            datetime.fromisoformat(attempt["timestamp"]) > cutoff_time
        ]
        
        # Brute force thresholds
        failed_threshold = 5  # 5 failed attempts
        time_window = 15      # in 15 minutes
        
        is_brute_force = len(recent_failures) >= failed_threshold
        
        return {
            "is_brute_force": is_brute_force,
            "failed_attempts": len(recent_failures),
            "threshold": failed_threshold,
            "time_window_minutes": time_window,
            "recent_attempts": recent_failures[-10:]  # Last 10 attempts
        }
    
    async def _check_credential_stuffing(
        self,
        ip_address: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Check for credential stuffing attacks."""
        # Get recent attempts from this IP across different usernames
        recent_attempts_key = f"login_attempts:{ip_address}"
        recent_attempts = await cache_service.get(recent_attempts_key) or []
        
        # Count unique usernames attempted in last hour
        cutoff_time = timestamp - timedelta(hours=1)
        recent_usernames = set()
        
        for attempt in recent_attempts:
            if datetime.fromisoformat(attempt["timestamp"]) > cutoff_time:
                recent_usernames.add(attempt["username"])
        
        # Credential stuffing thresholds
        username_threshold = 10  # 10 different usernames
        time_window = 60         # in 60 minutes
        
        is_credential_stuffing = len(recent_usernames) >= username_threshold
        
        return {
            "is_credential_stuffing": is_credential_stuffing,
            "unique_usernames": len(recent_usernames),
            "threshold": username_threshold,
            "time_window_minutes": time_window,
            "attempted_usernames": list(recent_usernames)[:20]  # First 20 usernames
        }
    
    async def _store_login_attempt(
        self,
        username: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        timestamp: datetime
    ):
        """Store login attempt for analysis."""
        attempt = {
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "timestamp": timestamp.isoformat()
        }
        
        # Store in IP-specific list
        ip_key = f"login_attempts:{ip_address}"
        ip_attempts = await cache_service.get(ip_key) or []
        ip_attempts.append(attempt)
        
        # Keep only last 100 attempts per IP
        ip_attempts = ip_attempts[-100:]
        await cache_service.set(ip_key, ip_attempts, ttl=86400)  # 24 hours
        
        # Store in global list for analysis
        global_key = "all_login_attempts"
        all_attempts = await cache_service.get(global_key) or []
        all_attempts.append(attempt)
        
        # Keep only last 1000 attempts globally
        all_attempts = all_attempts[-1000:]
        await cache_service.set(global_key, all_attempts, ttl=86400)
    
    def _get_security_recommendations(self, threats: List[Dict[str, Any]]) -> List[str]:
        """Get security recommendations based on detected threats."""
        recommendations = []
        
        threat_types = [threat["type"] for threat in threats]
        
        if SecurityEventType.BRUTE_FORCE_ATTEMPT.value in threat_types:
            recommendations.extend([
                "Implement account lockout after failed attempts",
                "Enable CAPTCHA for suspicious IPs",
                "Consider IP-based rate limiting"
            ])
        
        if SecurityEventType.MALICIOUS_IP.value in threat_types:
            recommendations.extend([
                "Block the malicious IP address",
                "Review firewall rules",
                "Enable geo-blocking if appropriate"
            ])
        
        if SecurityEventType.CREDENTIAL_STUFFING.value in threat_types:
            recommendations.extend([
                "Implement multi-factor authentication",
                "Force password resets for affected accounts",
                "Monitor for data breaches affecting your users"
            ])
        
        if SecurityEventType.SUSPICIOUS_LOGIN.value in threat_types:
            recommendations.extend([
                "Investigate the source of suspicious activity",
                "Review user agent filtering rules",
                "Consider additional authentication factors"
            ])
        
        return list(set(recommendations))  # Remove duplicates
    
    @cached(ttl=300, key_prefix="security_dashboard")
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data."""
        try:
            # Get recent login attempts
            all_attempts = await cache_service.get("all_login_attempts") or []
            
            # Analyze last 24 hours
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_attempts = [
                attempt for attempt in all_attempts
                if datetime.fromisoformat(attempt["timestamp"]) > cutoff_time
            ]
            
            # Calculate metrics
            total_attempts = len(recent_attempts)
            failed_attempts = len([a for a in recent_attempts if not a["success"]])
            success_rate = ((total_attempts - failed_attempts) / total_attempts * 100) if total_attempts > 0 else 0
            
            # Top attacking IPs
            ip_counter = Counter(attempt["ip_address"] for attempt in recent_attempts if not attempt["success"])
            top_attacking_ips = ip_counter.most_common(10)
            
            # Top targeted usernames
            username_counter = Counter(attempt["username"] for attempt in recent_attempts if not attempt["success"])
            top_targeted_usernames = username_counter.most_common(10)
            
            # Hourly attack distribution
            hourly_attacks = defaultdict(int)
            for attempt in recent_attempts:
                if not attempt["success"]:
                    hour = datetime.fromisoformat(attempt["timestamp"]).hour
                    hourly_attacks[hour] += 1
            
            return {
                "summary": {
                    "total_login_attempts_24h": total_attempts,
                    "failed_attempts_24h": failed_attempts,
                    "success_rate_percent": round(success_rate, 2),
                    "unique_ips_24h": len(set(a["ip_address"] for a in recent_attempts)),
                    "unique_usernames_24h": len(set(a["username"] for a in recent_attempts))
                },
                "threats": {
                    "top_attacking_ips": [
                        {"ip": ip, "attempts": count} for ip, count in top_attacking_ips
                    ],
                    "top_targeted_usernames": [
                        {"username": username, "attempts": count} for username, count in top_targeted_usernames
                    ]
                },
                "patterns": {
                    "hourly_attack_distribution": dict(hourly_attacks)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to generate security dashboard: {str(e)}"}
    
    async def analyze_request_content(self, content: str, content_type: str = "text") -> Dict[str, Any]:
        """Analyze request content for malicious patterns."""
        threats = []
        threat_level = ThreatLevel.LOW
        
        # Check for malicious patterns
        for pattern in self.threat_indicators["malicious_patterns"]:
            matches = re.findall(pattern, content)
            if matches:
                threats.append({
                    "type": "malicious_pattern",
                    "pattern": pattern,
                    "matches": matches[:5],  # First 5 matches
                    "description": f"Malicious pattern detected in {content_type}",
                    "severity": ThreatLevel.HIGH.value
                })
                threat_level = ThreatLevel.HIGH
        
        # Check content length (potential DoS)
        if len(content) > 1000000:  # 1MB
            threats.append({
                "type": "large_payload",
                "size": len(content),
                "description": "Unusually large payload detected",
                "severity": ThreatLevel.MEDIUM.value
            })
            if threat_level == ThreatLevel.LOW:
                threat_level = ThreatLevel.MEDIUM
        
        return {
            "threat_detected": len(threats) > 0,
            "threat_level": threat_level.value,
            "threats": threats,
            "content_size": len(content),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Get IP address reputation information."""
        try:
            # Validate IP address
            ip_obj = ipaddress.ip_address(ip_address)
            
            reputation = {
                "ip_address": ip_address,
                "is_private": ip_obj.is_private,
                "is_loopback": ip_obj.is_loopback,
                "is_multicast": ip_obj.is_multicast,
                "reputation_score": 100,  # Default good score
                "threat_indicators": [],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Check against known malicious IPs
            if ip_address in self.threat_indicators["malicious_ips"]:
                reputation["reputation_score"] = 0
                reputation["threat_indicators"].append({
                    "type": "known_malicious",
                    "description": "IP is in known malicious IP list",
                    "severity": ThreatLevel.CRITICAL.value
                })
            
            # Check recent activity
            recent_attempts_key = f"login_attempts:{ip_address}"
            recent_attempts = await cache_service.get(recent_attempts_key) or []
            
            if recent_attempts:
                failed_attempts = len([a for a in recent_attempts if not a["success"]])
                total_attempts = len(recent_attempts)
                
                if total_attempts > 0:
                    failure_rate = failed_attempts / total_attempts
                    
                    if failure_rate > 0.8:  # 80% failure rate
                        reputation["reputation_score"] -= 50
                        reputation["threat_indicators"].append({
                            "type": "high_failure_rate",
                            "description": f"High login failure rate: {failure_rate:.1%}",
                            "severity": ThreatLevel.HIGH.value
                        })
                    
                    if total_attempts > 50:  # High volume
                        reputation["reputation_score"] -= 30
                        reputation["threat_indicators"].append({
                            "type": "high_volume",
                            "description": f"High volume of attempts: {total_attempts}",
                            "severity": ThreatLevel.MEDIUM.value
                        })
            
            reputation["reputation_score"] = max(0, reputation["reputation_score"])
            
            return reputation
            
        except ValueError:
            return {
                "error": f"Invalid IP address: {ip_address}",
                "ip_address": ip_address
            }
    
    async def block_ip(self, ip_address: str, reason: str, duration_hours: int = 24) -> Dict[str, Any]:
        """Block an IP address."""
        try:
            # Validate IP
            ipaddress.ip_address(ip_address)
            
            block_entry = {
                "ip_address": ip_address,
                "reason": reason,
                "blocked_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=duration_hours)).isoformat(),
                "duration_hours": duration_hours
            }
            
            # Store in blocked IPs list
            blocked_ips_key = "blocked_ips"
            blocked_ips = await cache_service.get(blocked_ips_key) or {}
            blocked_ips[ip_address] = block_entry
            
            await cache_service.set(blocked_ips_key, blocked_ips, ttl=duration_hours * 3600)
            
            return {
                "success": True,
                "message": f"IP {ip_address} blocked for {duration_hours} hours",
                "block_details": block_entry
            }
            
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid IP address: {ip_address}"
            }
    
    async def is_ip_blocked(self, ip_address: str) -> Dict[str, Any]:
        """Check if an IP address is blocked."""
        blocked_ips = await cache_service.get("blocked_ips") or {}
        
        if ip_address in blocked_ips:
            block_info = blocked_ips[ip_address]
            expires_at = datetime.fromisoformat(block_info["expires_at"])
            
            if datetime.now(timezone.utc) < expires_at:
                return {
                    "is_blocked": True,
                    "block_info": block_info,
                    "time_remaining": str(expires_at - datetime.now(timezone.utc))
                }
            else:
                # Block expired, remove it
                del blocked_ips[ip_address]
                await cache_service.set("blocked_ips", blocked_ips, ttl=86400)
        
        return {"is_blocked": False}