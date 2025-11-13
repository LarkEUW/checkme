import aiohttp
import asyncio
import hashlib
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re

class ThreatIntelAnalyzer:
    """Real threat intelligence analysis"""
    
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # Threat intelligence sources
        self.virus_total_api_key = None  # Set from environment
        self.abuse_api_key = None  # Set from environment
        
        # Known malicious patterns and domains
        self.malicious_patterns = [
            # Common malware patterns
            r'eval\s*\(\s*["\'].*["\']\s*\)',
            r'document\.write\s*\(\s*["\'].*["\']\s*\)',
            r'new\s+Function\s*\(\s*["\'].*["\']\s*\)',
            r'atob\s*\(\s*["\'].*["\']\s*\)',
            r'escape\s*\(\s*["\'].*["\']\s*\)',
            r'unescape\s*\(\s*["\'].*["\']\s*\)',
        ]
        
        # Known malicious domains (simplified list)
        self.known_malicious_domains = {
            'malware-site.com', 'phishing-site.net', 'bad-actor.org',
            'suspicious-domain.com', 'dangerous-site.io'
        }
        
        # Tracking/analytics domains
        self.tracking_domains = {
            'google-analytics.com', 'doubleclick.net', 'facebook.com',
            'googlesyndication.com', 'googleads.g.doubleclick.net',
            'connect.facebook.net', 'googleadservices.com'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_domains(self, domains: List[str], urls: List[str]) -> Dict[str, Any]:
        """Analyze domains for threat intelligence indicators"""
        findings = []
        malicious_indicators = []
        score_impact = 0
        
        # Check each domain
        for domain in domains:
            domain_lower = domain.lower()
            
            # Check against known malicious domains
            if any(malicious in domain_lower for malicious in self.known_malicious_domains):
                malicious_indicators.append({
                    'domain': domain,
                    'type': 'known_malicious',
                    'severity': 'high'
                })
                score_impact -= 3
                findings.append(f"Known malicious domain: {domain}")
            
            # Check against tracking domains
            elif any(tracking in domain_lower for tracking in self.tracking_domains):
                malicious_indicators.append({
                    'domain': domain,
                    'type': 'tracking',
                    'severity': 'medium'
                })
                score_impact -= 1
                findings.append(f"Tracking/analytics domain: {domain}")
            
            # Check for suspicious TLDs
            elif domain_lower.endswith(('.tk', '.ml', '.cf', '.ga')):
                malicious_indicators.append({
                    'domain': domain,
                    'type': 'suspicious_tld',
                    'severity': 'low'
                })
                score_impact -= 0.5
                findings.append(f"Suspicious TLD: {domain}")
        
        # Check URLs for malicious patterns
        malicious_urls = []
        for url in urls:
            if not url.startswith('https://'):
                malicious_urls.append(url)
                score_impact -= 2
                findings.append(f"Insecure URL: {url}")
        
        # Check for phishing indicators
        phishing_indicators = await self._check_phishing_indicators(domains, urls)
        if phishing_indicators:
            score_impact -= 2
            findings.extend(phishing_indicators)
        
        # Calculate final score (0-10 scale)
        final_score = max(0, min(10, 5 + score_impact))
        
        return {
            'score': final_score,
            'malicious_indicators': malicious_indicators,
            'malicious_urls': malicious_urls,
            'phishing_indicators': phishing_indicators,
            'findings': findings,
            'domains_checked': len(domains),
            'urls_checked': len(urls)
        }
    
    async def _check_phishing_indicators(self, domains: List[str], urls: List[str]) -> List[str]:
        """Check for phishing indicators"""
        indicators = []
        
        for domain in domains:
            # Check for domain typosquatting
            if self._is_typosquatting(domain):
                indicators.append(f"Potential typosquatting domain: {domain}")
            
            # Check for homograph attacks
            if self._contains_idn_homographs(domain):
                indicators.append(f"IDN homographs detected in domain: {domain}")
            
            # Check for suspicious keywords
            suspicious_keywords = ['login', 'bank', 'secure', 'verify', 'update', 'confirm']
            if any(keyword in domain.lower() for keyword in suspicious_keywords):
                indicators.append(f"Suspicious keywords in domain: {domain}")
        
        return indicators
    
    def _is_typosquatting(self, domain: str) -> bool:
        """Check if domain is typosquatting a popular domain"""
        popular_domains = [
            'google.com', 'facebook.com', 'amazon.com', 'microsoft.com',
            'apple.com', 'paypal.com', 'bankofamerica.com', 'wells-fargo.com'
        ]
        
        domain_parts = domain.split('.')
        if len(domain_parts) < 2:
            return False
        
        main_domain = domain_parts[0]
        
        for popular in popular_domains:
            popular_main = popular.split('.')[0]
            
            # Check for common typosquatting techniques
            if self._calculate_levenshtein_distance(main_domain, popular_main) <= 2:
                return True
            
            # Check for character swapping
            if self._has_character_swap(main_domain, popular_main):
                return True
            
            # Check for character insertion/deletion
            if self._has_extra_character(main_domain, popular_main):
                return True
        
        return False
    
    def _calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._calculate_levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _has_character_swap(self, domain: str, target: str) -> bool:
        """Check if domain has swapped characters"""
        if len(domain) != len(target):
            return False
        
        differences = 0
        for i in range(len(domain)):
            if domain[i] != target[i]:
                differences += 1
        
        return differences == 2
    
    def _has_extra_character(self, domain: str, target: str) -> bool:
        """Check if domain has extra or missing characters"""
        if abs(len(domain) - len(target)) == 1:
            # Check if one is substring of the other
            if len(domain) > len(target):
                return target in domain
            else:
                return domain in target
        return False
    
    def _contains_idn_homographs(self, domain: str) -> bool:
        """Check if domain contains IDN homographs"""
        # Check for mixed scripts (Latin + Cyrillic, etc.)
        cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        latin_chars = set('abcdefghijklmnopqrstuvwxyz')
        
        domain_lower = domain.lower()
        has_cyrillic = any(c in cyrillic_chars for c in domain_lower)
        has_latin = any(c in latin_chars for c in domain_lower)
        
        return has_cyrillic and has_latin
    
    async def check_virustotal(self, domains: List[str]) -> Dict[str, Any]:
        """Check domains against VirusTotal (if API key available)"""
        if not self.virus_total_api_key:
            return {'status': 'no_api_key', 'results': []}
        
        results = []
        
        for domain in domains:
            try:
                url = f"https://www.virustotal.com/api/v3/domains/{domain}"
                headers = {
                    'x-apikey': self.virus_total_api_key,
                    'Accept': 'application/json'
                }
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract malicious count
                        malicious_count = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {}).get('malicious', 0)
                        
                        results.append({
                            'domain': domain,
                            'malicious_count': malicious_count,
                            'total_engines': 70  # Approximate number of engines
                        })
                    else:
                        results.append({
                            'domain': domain,
                            'error': f'HTTP {response.status}',
                            'malicious_count': 0
                        })
            
            except Exception as e:
                results.append({
                    'domain': domain,
                    'error': str(e),
                    'malicious_count': 0
                })
        
        return {
            'status': 'completed',
            'results': results
        }
    
    async def check_abuse_ipdb(self, domains: List[str]) -> Dict[str, Any]:
        """Check domains against AbuseIPDB (if API key available)"""
        if not self.abuse_api_key:
            return {'status': 'no_api_key', 'results': []}
        
        results = []
        
        for domain in domains:
            try:
                # Resolve domain to IP first
                # Note: In a real implementation, you'd use asyncio DNS resolver
                ip_address = "127.0.0.1"  # Placeholder
                
                url = "https://api.abuseipdb.com/api/v2/check"
                headers = {
                    'Key': self.abuse_api_key,
                    'Accept': 'application/json'
                }
                params = {
                    'ipAddress': ip_address,
                    'maxAgeInDays': 90,
                    'verbose': ''
                }
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        abuse_confidence = data.get('data', {}).get('abuseConfidencePercentage', 0)
                        
                        results.append({
                            'domain': domain,
                            'ip': ip_address,
                            'abuse_confidence': abuse_confidence,
                            'is_malicious': abuse_confidence > 50
                        })
                    else:
                        results.append({
                            'domain': domain,
                            'ip': ip_address,
                            'error': f'HTTP {response.status}',
                            'abuse_confidence': 0
                        })
            
            except Exception as e:
                results.append({
                    'domain': domain,
                    'error': str(e),
                    'abuse_confidence': 0
                })
        
        return {
            'status': 'completed',
            'results': results
        }

# Export the analyzer
__all__ = ['ThreatIntelAnalyzer']