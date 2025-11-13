import json
import re
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
import zipfile
import tempfile
import os
from pathlib import Path
from extension_downloader import ExtensionDownloader
from threat_intel import ThreatIntelAnalyzer
from ai_analyzer import AIAnalyzer

@dataclass
class AnalysisResult:
    score: float  # 0-10
    data: Dict[str, Any]
    findings: List[Dict[str, Any]]

class MetadataAnalyzer:
    """Analyzes extension metadata from store or file"""
    
    def __init__(self):
        self.bonuses = {}
        self.maluses = {}
    
    async def analyze(self, manifest: Dict[str, Any], store_data: Optional[Dict] = None) -> AnalysisResult:
        findings = []
        score = 5.0  # Start neutral
        
        if store_data:
            # Analyze store metadata
            rating = store_data.get('rating', 0)
            users = store_data.get('users', 0)
            last_update = store_data.get('last_updated')
            
            # Rating analysis
            if rating >= 4.0:
                score += 1
                findings.append({
                    'type': 'positive',
                    'message': f'High rating: {rating}/5',
                    'severity': 'low'
                })
            elif rating < 3.0:
                score -= 1
                findings.append({
                    'type': 'negative',
                    'message': f'Low rating: {rating}/5',
                    'severity': 'medium'
                })
            
            # User base analysis
            if users > 100000:
                score += 1
                findings.append({
                    'type': 'positive',
                    'message': f'Large user base: {users:,} users',
                    'severity': 'low'
                })
            
            # Update frequency
            if last_update:
                update_date = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                months_since_update = (datetime.now() - update_date).days / 30
                
                if months_since_update > 36:
                    score -= 3
                    self.maluses['outdated_36m'] = -3
                    findings.append({
                        'type': 'negative',
                        'message': f'Very outdated: {months_since_update:.1f} months since update',
                        'severity': 'high'
                    })
                elif months_since_update > 18:
                    score -= 1.5
                    self.maluses['outdated_18m'] = -1.5
                    findings.append({
                        'type': 'negative',
                        'message': f'Outdated: {months_since_update:.1f} months since update',
                        'severity': 'medium'
                    })
            
            # Developer verification
            if store_data.get('verified_publisher'):
                score += 2
                self.bonuses['verified_publisher'] = 2
                findings.append({
                    'type': 'positive',
                    'message': 'Verified publisher badge',
                    'severity': 'low'
                })
            
            if store_data.get('duns_number'):
                score += 2
                self.bonuses['duns_number'] = 2
                findings.append({
                    'type': 'positive',
                    'message': 'D-U-N-S number present',
                    'severity': 'low'
                })
        
        # Manifest analysis
        version = manifest.get('version', '0.0.0')
        name = manifest.get('name', 'Unknown')
        
        # Basic metadata checks
        if not manifest.get('description'):
            score -= 0.5
            findings.append({
                'type': 'negative',
                'message': 'Missing description in manifest',
                'severity': 'low'
            })
        
        if not manifest.get('author'):
            score -= 0.5
            findings.append({
                'type': 'negative',
                'message': 'Missing author information',
                'severity': 'low'
            })
        
        # Clamp score to 0-10 range
        score = max(0, min(10, score))
        
        return AnalysisResult(
            score=score,
            data={
                'name': name,
                'version': version,
                'author': manifest.get('author'),
                'description': manifest.get('description'),
                'store_data': store_data,
                'bonuses': self.bonuses,
                'maluses': self.maluses
            },
            findings=findings
        )

class PermissionAnalyzer:
    """Analyzes extension permissions for risk assessment"""
    
    PERMISSION_RISKS = {
        # Critical permissions
        'activeTab': {'risk': 'low', 'category': 'tabs'},
        'tabs': {'risk': 'medium', 'category': 'tabs'},
        'background': {'risk': 'low', 'category': 'background'},
        'bookmarks': {'risk': 'medium', 'category': 'bookmarks'},
        'browsingData': {'risk': 'high', 'category': 'privacy'},
        'clipboardRead': {'risk': 'medium', 'category': 'clipboard'},
        'clipboardWrite': {'risk': 'low', 'category': 'clipboard'},
        'contentSettings': {'risk': 'medium', 'category': 'settings'},
        'contextMenus': {'risk': 'low', 'category': 'ui'},
        'cookies': {'risk': 'high', 'category': 'cookies'},
        'debugger': {'risk': 'critical', 'category': 'development'},
        'declarativeContent': {'risk': 'low', 'category': 'content'},
        'declarativeNetRequest': {'risk': 'medium', 'category': 'network'},
        'downloads': {'risk': 'medium', 'category': 'downloads'},
        'downloads.open': {'risk': 'medium', 'category': 'downloads'},
        'history': {'risk': 'high', 'category': 'privacy'},
        'identity': {'risk': 'medium', 'category': 'identity'},
        'idle': {'risk': 'low', 'category': 'system'},
        'management': {'risk': 'medium', 'category': 'extension_management'},
        'notifications': {'risk': 'low', 'category': 'notifications'},
        'pageCapture': {'risk': 'medium', 'category': 'capture'},
        'power': {'risk': 'low', 'category': 'system'},
        'printerProvider': {'risk': 'medium', 'category': 'printing'},
        'privacy': {'risk': 'high', 'category': 'privacy'},
        'proxy': {'risk': 'high', 'category': 'network'},
        'scripting': {'risk': 'medium', 'category': 'content_scripts'},
        'search': {'risk': 'medium', 'category': 'search'},
        'sessions': {'risk': 'medium', 'category': 'sessions'},
        'storage': {'risk': 'low', 'category': 'storage'},
        'system.cpu': {'risk': 'low', 'category': 'system'},
        'system.memory': {'risk': 'low', 'category': 'system'},
        'system.storage': {'risk': 'medium', 'category': 'system'},
        'tabCapture': {'risk': 'high', 'category': 'capture'},
        'topSites': {'risk': 'medium', 'category': 'privacy'},
        'unlimitedStorage': {'risk': 'low', 'category': 'storage'},
        'vpnProvider': {'risk': 'high', 'category': 'network'},
        'wallpaper': {'risk': 'low', 'category': 'appearance'},
        'webNavigation': {'risk': 'high', 'category': 'navigation'},
        'webRequest': {'risk': 'high', 'category': 'network'},
        'webRequestBlocking': {'risk': 'critical', 'category': 'network'},
    }
    
    async def analyze(self, manifest: Dict[str, Any]) -> AnalysisResult:
        permissions = manifest.get('permissions', [])
        host_permissions = manifest.get('host_permissions', [])
        optional_permissions = manifest.get('optional_permissions', [])
        
        all_permissions = permissions + host_permissions + optional_permissions
        findings = []
        score = 5.0
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for perm in all_permissions:
            if isinstance(perm, str):
                perm_name = perm
            else:
                perm_name = perm.get('permission', str(perm))
            
            # Check against known permission risks
            if perm_name in self.PERMISSION_RISKS:
                risk_info = self.PERMISSION_RISKS[perm_name]
                risk_level = risk_info['risk']
                risk_counts[risk_level] += 1
                
                if risk_level == 'critical':
                    score -= 2
                    findings.append({
                        'type': 'negative',
                        'message': f'Critical permission: {perm_name}',
                        'severity': 'critical',
                        'category': risk_info['category']
                    })
                elif risk_level == 'high':
                    score -= 1
                    findings.append({
                        'type': 'negative',
                        'message': f'High-risk permission: {perm_name}',
                        'severity': 'high',
                        'category': risk_info['category']
                    })
                elif risk_level == 'medium':
                    score -= 0.5
                    findings.append({
                        'type': 'negative',
                        'message': f'Medium-risk permission: {perm_name}',
                        'severity': 'medium',
                        'category': risk_info['category']
                    })
            
            # Check for host permissions (broad access)
            if perm.startswith('http') and ('*' in perm or perm.count('/') < 4):
                score -= 1.5
                findings.append({
                    'type': 'negative',
                    'message': f'Broad host permission: {perm}',
                    'severity': 'high',
                    'category': 'host_permissions'
                })
        
        # Positive findings for minimal permissions
        if risk_counts['critical'] == 0 and risk_counts['high'] == 0:
            score += 2
            findings.append({
                'type': 'positive',
                'message': 'No critical or high-risk permissions',
                'severity': 'low'
            })
        
        # Clamp score
        score = max(0, min(10, score))
        
        return AnalysisResult(
            score=score,
            data={
                'permissions': permissions,
                'host_permissions': host_permissions,
                'optional_permissions': optional_permissions,
                'risk_distribution': risk_counts,
                'total_permissions': len(all_permissions)
            },
            findings=findings
        )

class CodeBehaviorAnalyzer:
    """Analyzes code patterns for malicious behaviors"""
    
    BEHAVIOR_PATTERNS = [
        # Obfuscation patterns
        {
            'name': 'Base64 encoding',
            'pattern': r'atob\s*\(|btoa\s*\(|Base64\.decode|Base64\.encode',
            'category': 'obfuscation',
            'severity': 'medium'
        },
        {
            'name': 'String concatenation obfuscation',
            'pattern': r'["\']\s*\+\s*["\'].*["\']\s*\+\s*["\']',
            'category': 'obfuscation',
            'severity': 'low'
        },
        {
            'name': 'Hex encoding',
            'pattern': r'\\x[0-9a-fA-F]{2}',
            'category': 'obfuscation',
            'severity': 'medium'
        },
        # Tracking/Fingerprinting
        {
            'name': 'Canvas fingerprinting',
            'pattern': r'canvas.*toDataURL|getImageData.*canvas',
            'category': 'tracking',
            'severity': 'high'
        },
        {
            'name': 'WebRTC IP leak',
            'pattern': r'RTCPeerConnection|createDataChannel',
            'category': 'tracking',
            'severity': 'high'
        },
        {
            'name': 'User agent tracking',
            'pattern': r'navigator\.userAgent|navigator\.platform',
            'category': 'tracking',
            'severity': 'low'
        },
        # Data Exfiltration
        {
            'name': 'External POST requests',
            'pattern': r'fetch\s*\([^)]*\)\s*\.then|XMLHttpRequest.*POST',
            'category': 'exfiltration',
            'severity': 'medium'
        },
        {
            'name': 'Form data collection',
            'pattern': r'FormData|new\s+FormData',
            'category': 'exfiltration',
            'severity': 'medium'
        },
        # Dangerous APIs
        {
            'name': 'eval usage',
            'pattern': r'eval\s*\(|new\s+Function\s*\(',
            'category': 'dangerous_api',
            'severity': 'high'
        },
        {
            'name': 'setTimeout with string',
            'pattern': r'setTimeout\s*\(\s*["\']',
            'category': 'dangerous_api',
            'severity': 'medium'
        },
        # Code Injection
        {
            'name': 'innerHTML with variables',
            'pattern': r'innerHTML\s*=.*\+|outerHTML\s*=.*\+',
            'category': 'injection',
            'severity': 'high'
        },
        {
            'name': 'document.write',
            'pattern': r'document\.write',
            'category': 'injection',
            'severity': 'medium'
        }
    ]
    
    async def analyze(self, manifest: Dict[str, Any], file_path: str) -> AnalysisResult:
        findings = []
        score = 5.0
        total_matches = 0
        
        # Get all JavaScript files from the extension
        js_files = await self._extract_js_files(file_path)
        
        for file_info in js_files:
            content = file_info['content']
            file_name = file_info['name']
            
            for pattern in self.BEHAVIOR_PATTERNS:
                matches = re.findall(pattern['pattern'], content, re.IGNORECASE)
                if matches:
                    total_matches += len(matches)
                    
                    if pattern['severity'] == 'high':
                        score -= 1.5
                    elif pattern['severity'] == 'medium':
                        score -= 1
                    elif pattern['severity'] == 'low':
                        score -= 0.5
                    
                    findings.append({
                        'type': 'negative',
                        'message': f"{pattern['name']} detected in {file_name}",
                        'severity': pattern['severity'],
                        'category': pattern['category'],
                        'file': file_name,
                        'matches': len(matches),
                        'pattern': pattern['pattern']
                    })
        
        # Additional checks
        if total_matches > 10:
            score -= 2
            findings.append({
                'type': 'negative',
                'message': f'High number of suspicious patterns: {total_matches}',
                'severity': 'high',
                'category': 'overall'
            })
        
        # Clamp score
        score = max(0, min(10, score))
        
        return AnalysisResult(
            score=score,
            data={
                'total_files_analyzed': len(js_files),
                'total_patterns_found': total_matches,
                'files': [f['name'] for f in js_files]
            },
            findings=findings
        )
    
    async def _extract_js_files(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract JavaScript files from extension package"""
        js_files = []
        
        if os.path.isdir(file_path):
            # Handle extracted directory
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    if file.endswith('.js'):
                        file_full_path = os.path.join(root, file)
                        try:
                            with open(file_full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                js_files.append({
                                    'name': os.path.relpath(file_full_path, file_path),
                                    'content': content,
                                    'size': len(content)
                                })
                        except Exception:
                            continue
        
        return js_files

class NetworkAnalyzer:
    """Analyzes network requests and data flows"""
    
    async def analyze(self, manifest: Dict[str, Any], file_path: str) -> AnalysisResult:
        findings = []
        score = 5.0
        
        # Extract URLs from JavaScript files
        js_files = await self._extract_js_files(file_path)
        all_urls = []
        
        url_pattern = r'https?://[^\s"\'<>]+'
        
        for file_info in js_files:
            content = file_info['content']
            urls = re.findall(url_pattern, content)
            all_urls.extend(urls)
        
        # Analyze URLs
        external_urls = [url for url in all_urls if not any(local in url for local in ['localhost', '127.0.0.1', 'chrome-extension'])']
        unique_domains = list(set([url.split('/')[2] for url in external_urls]))
        
        # Check for non-HTTPS URLs
        http_urls = [url for url in external_urls if url.startswith('http://')]
        if http_urls:
            score -= 2
            findings.append({
                'type': 'negative',
                'message': f'Insecure HTTP URLs found: {len(http_urls)}',
                'severity': 'high',
                'urls': http_urls[:5]  # Limit for display
            })
        
        # Check for tracking/analytics domains
        tracking_domains = ['google-analytics', 'doubleclick', 'facebook', 'mixpanel', 'segment']
        found_tracking = [domain for domain in unique_domains if any(track in domain.lower() for track in tracking_domains)]
        if found_tracking:
            score -= 1
            findings.append({
                'type': 'negative',
                'message': f'Tracking/analytics domains found: {len(found_tracking)}',
                'severity': 'medium',
                'domains': found_tracking
            })
        
        # Check for many external domains
        if len(unique_domains) > 10:
            score -= 1
            findings.append({
                'type': 'negative',
                'message': f'Many external domains: {len(unique_domains)}',
                'severity': 'medium'
            })
        
        # Positive findings
        if len(external_urls) == 0:
            score += 2
            findings.append({
                'type': 'positive',
                'message': 'No external network requests',
                'severity': 'low'
            })
        elif len(unique_domains) <= 3 and len(http_urls) == 0:
            score += 1
            findings.append({
                'type': 'positive',
                'message': 'Limited and secure external connections',
                'severity': 'low'
            })
        
        # Clamp score
        score = max(0, min(10, score))
        
        return AnalysisResult(
            score=score,
            data={
                'total_urls': len(all_urls),
                'external_urls': len(external_urls),
                'unique_domains': len(unique_domains),
                'http_urls': len(http_urls),
                'tracking_domains': len(found_tracking),
                'domains': unique_domains[:20]  # Limit for storage
            },
            findings=findings
        )
    
    async def _extract_js_files(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract JavaScript files from extension package"""
        js_files = []
        
        if os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    if file.endswith('.js'):
                        file_full_path = os.path.join(root, file)
                        try:
                            with open(file_full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                js_files.append({
                                    'name': os.path.relpath(file_full_path, file_path),
                                    'content': content
                                })
                        except Exception:
                            continue
        
        return js_files

class ThreatIntelAnalyzer:
    """Analyzes threat intelligence data"""
    
    def __init__(self):
        from threat_intel import ThreatIntelAnalyzer as RealThreatIntelAnalyzer
        self.analyzer = RealThreatIntelAnalyzer()
    
    async def analyze(self, domains: List[str], urls: List[str]) -> AnalysisResult:
        try:
            async with self.analyzer as intel_analyzer:
                result = await intel_analyzer.analyze_domains(domains, urls)
                
                # Convert to AnalysisResult format
                score = result['score']
                findings = []
                
                for finding in result['findings']:
                    findings.append({
                        'type': 'negative',
                        'message': finding,
                        'severity': 'medium'
                    })
                
                return AnalysisResult(
                    score=score,
                    data=result,
                    findings=findings
                )
        except Exception:
            # Fallback to safe score on error
            return AnalysisResult(
                score=5.0,
                data={'error': 'Threat intel analysis failed'},
                findings=[]
            )

class CVEAnalyzer:
    """Analyzes CVE vulnerabilities in dependencies"""
    
    async def analyze(self, manifest: Dict[str, Any], js_files: List[Dict]) -> AnalysisResult:
        findings = []
        score = 5.0
        
        # Extract library information from JavaScript files
        libraries = []
        
        # Common library patterns
        library_patterns = {
            'jquery': r'jQuery\s*v?(\d+\.\d+\.\d+)',
            'lodash': r'lodash\s*v?(\d+\.\d+\.\d+)',
            'moment': r'Moment\.js\s*v?(\d+\.\d+\.\d+)',
            'axios': r'axios\s*v?(\d+\.\d+\.\d+)',
            'vue': r'Vue\s*v?(\d+\.\d+\.\d+)',
            'react': r'React\s*v?(\d+\.\d+\.\d+)'
        }
        
        for file_info in js_files:
            content = file_info['content']
            for lib_name, pattern in library_patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    libraries.append({
                        'name': lib_name,
                        'version': matches[0] if matches else 'unknown',
                        'file': file_info['name']
                    })
        
        # Mock CVE database lookup
        # In production, this would query NVD API
        mock_cves = []
        
        # Simulate finding some CVEs for demo purposes
        import random
        if libraries and random.random() < 0.3:  # 30% chance for demo
            lib = libraries[0]
            mock_cves.append({
                'id': 'CVE-2023-1234',
                'library': lib['name'],
                'version': lib['version'],
                'severity': 'high',
                'description': 'Example vulnerability for demonstration'
            })
        
        if mock_cves:
            score -= 3
            findings.append({
                'type': 'negative',
                'message': f'CVE vulnerabilities found: {len(mock_cves)}',
                'severity': 'high',
                'cves': mock_cves
            })
        else:
            score += 1
            findings.append({
                'type': 'positive',
                'message': 'No known CVE vulnerabilities found',
                'severity': 'low'
            })
        
        # Clamp score
        score = max(0, min(10, score))
        
        return AnalysisResult(
            score=score,
            data={
                'libraries_found': libraries,
                'cve_count': len(mock_cves),
                'cves': mock_cves
            },
            findings=findings
        )

class AIAnalyzer:
    """AI-powered analysis for contextual insights"""
    
    def __init__(self):
        from ai_analyzer import AIAnalyzer as RealAIAnalyzer
        self.analyzer = RealAIAnalyzer()
    
    async def analyze(self, all_results: Dict[str, AnalysisResult]) -> AnalysisResult:
        try:
            result = self.analyzer.analyze(all_results)
            
            # Convert to AnalysisResult format
            score = result['score']
            findings = []
            
            # Add findings based on risk level
            risk_level = result['risk_level']
            if risk_level in ['high', 'critical']:
                findings.append({
                    'type': 'negative',
                    'message': f'AI analysis identified {risk_level} risk factors',
                    'severity': risk_level,
                    'recommendation': 'Review AI recommendations carefully'
                })
            else:
                findings.append({
                    'type': 'positive',
                    'message': 'AI analysis shows manageable risk profile',
                    'severity': 'low',
                    'recommendation': 'Standard security practices recommended'
                })
            
            return AnalysisResult(
                score=score,
                data=result,
                findings=findings
            )
        except Exception:
            # Fallback to neutral score on error
            return AnalysisResult(
                score=5.0,
                data={'error': 'AI analysis failed'},
                findings=[]
            )

class AnalysisEngine:
    """Main analysis engine that orchestrates all analyzers"""
    
    def __init__(self):
        self.analyzers = {
            'metadata': MetadataAnalyzer(),
            'permissions': PermissionAnalyzer(),
            'code_behavior': CodeBehaviorAnalyzer(),
            'network': NetworkAnalyzer(),
            'threat_intel': ThreatIntelAnalyzer(),
            'cve': CVEAnalyzer(),
            'ai': AIAnalyzer()
        }
        
        # Weight configuration (sum should be 1.0)
        self.weights = {
            'metadata': 0.15,
            'permissions': 0.20,
            'code_behavior': 0.25,
            'network': 0.15,
            'threat_intel': 0.10,
            'cve': 0.10,
            'ai': 0.05
        }
    
    async def analyze_extension(self, manifest: Dict[str, Any], file_path: str, store_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Run complete analysis on an extension"""
        
        # Run all analyzers
        results = {}
        
        # Metadata analysis
        results['metadata'] = await self.analyzers['metadata'].analyze(manifest, store_data)
        
        # Permission analysis
        results['permissions'] = await self.analyzers['permissions'].analyze(manifest)
        
        # Code behavior analysis
        results['code_behavior'] = await self.analyzers['code_behavior'].analyze(manifest, file_path)
        
        # Network analysis
        results['network'] = await self.analyzers['network'].analyze(manifest, file_path)
        
        # Extract domains for threat intel
        network_data = results['network'].data
        domains = network_data.get('domains', [])
        
        # Threat intelligence analysis
        results['threat_intel'] = await self.analyzers['threat_intel'].analyze(domains, [])
        
        # CVE analysis
        js_files = await self.analyzers['code_behavior']._extract_js_files(file_path)
        results['cve'] = await self.analyzers['cve'].analyze(manifest, js_files)
        
        # AI analysis
        results['ai'] = await self.analyzers['ai'].analyze(results)
        
        # Calculate final score
        final_score = 0.0
        for analyzer_name, result in results.items():
            if analyzer_name in self.weights:
                final_score += result.score * self.weights[analyzer_name]
        
        # Apply bonuses and maluses
        metadata_data = results['metadata'].data
        bonuses = metadata_data.get('bonuses', {})
        maluses = metadata_data.get('maluses', {})
        
        bonus_total = sum(bonuses.values())
        malus_total = sum(maluses.values())
        
        final_score += bonus_total + malus_total
        
        # Clamp to 0-50 range
        final_score = max(0, min(50, final_score))
        
        # Determine verdict
        if final_score <= 10:
            verdict = 'safe'
        elif final_score <= 25:
            verdict = 'needs_review'
        elif final_score <= 40:
            verdict = 'high_risk'
        else:
            verdict = 'block'
        
        return {
            'scores': {name: result.score for name, result in results.items()},
            'final_score': final_score,
            'verdict': verdict,
            'results': {name: {
                'score': result.score,
                'data': result.data,
                'findings': result.findings
            } for name, result in results.items()},
            'bonuses': bonuses,
            'maluses': maluses
        }