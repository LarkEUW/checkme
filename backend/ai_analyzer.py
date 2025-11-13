import json
from typing import Dict, List, Any, Optional
import re

class AIAnalyzer:
    """AI-powered analysis for contextual insights and recommendations"""
    
    def __init__(self):
        self.risk_categories = {
            'low': {
                'threshold': 3,
                'description': 'Minimal security risk',
                'recommendations': [
                    'Extension appears safe for general use',
                    'Standard security practices recommended',
                    'Regular updates should be maintained'
                ]
            },
            'medium': {
                'threshold': 6,
                'description': 'Moderate security concerns',
                'recommendations': [
                    'Review extension permissions carefully',
                    'Consider if the functionality justifies the risks',
                    'Monitor extension behavior in production'
                ]
            },
            'high': {
                'threshold': 8,
                'description': 'Significant security risks',
                'recommendations': [
                    'Extension poses notable security risks',
                    'Careful consideration required before installation',
                    'Implement additional monitoring and restrictions'
                ]
            },
            'critical': {
                'threshold': 10,
                'description': 'Severe security threats',
                'recommendations': [
                    'Extension poses serious security threats',
                    'Strongly recommend against installation',
                    'If required, isolate in restricted environment'
                ]
            }
        }
    
    def analyze(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights and recommendations"""
        
        # Extract scores from all modules
        scores = {
            'metadata': all_results.get('metadata', {}).get('score', 0),
            'permissions': all_results.get('permissions', {}).get('score', 0),
            'code_behavior': all_results.get('code_behavior', {}).get('score', 0),
            'network': all_results.get('network', {}).get('score', 0),
            'threat_intel': all_results.get('threat_intel', {}).get('score', 0),
            'cve': all_results.get('cve', {}).get('score', 0)
        }
        
        # Calculate weighted risk score
        weighted_score = self._calculate_weighted_risk(scores)
        
        # Generate contextual analysis
        context_analysis = self._generate_contextual_analysis(all_results, scores)
        
        # Generate attack scenarios
        attack_scenarios = self._generate_attack_scenarios(all_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(weighted_score, all_results)
        
        # Generate summary
        summary = self._generate_summary(weighted_score, all_results)
        
        return {
            'score': weighted_score,
            'risk_level': self._get_risk_level(weighted_score),
            'contextual_analysis': context_analysis,
            'attack_scenarios': attack_scenarios,
            'recommendations': recommendations,
            'summary': summary,
            'explanations': self._generate_explanations(scores, all_results)
        }
    
    def _calculate_weighted_risk(self, scores: Dict[str, float]) -> float:
        """Calculate weighted risk score based on module scores"""
        weights = {
            'metadata': 0.15,
            'permissions': 0.20,
            'code_behavior': 0.25,
            'network': 0.15,
            'threat_intel': 0.15,
            'cve': 0.10
        }
        
        weighted_score = 0
        for module, score in scores.items():
            weight = weights.get(module, 0)
            # Convert 0-10 score to risk (higher score = higher risk)
            risk_contribution = (score / 10) * weight * 10
            weighted_score += risk_contribution
        
        return min(10, weighted_score)
    
    def _generate_contextual_analysis(self, all_results: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Generate contextual analysis based on findings"""
        analysis = []
        
        # Analyze permissions
        if scores['permissions'] > 7:
            analysis.append("The extension requests extensive permissions that could pose significant security risks. These permissions may allow access to sensitive user data or system resources.")
        elif scores['permissions'] < 3:
            analysis.append("The extension requests minimal permissions, following the principle of least privilege. This is a positive security indicator.")
        
        # Analyze code behavior
        if scores['code_behavior'] > 7:
            code_findings = all_results.get('code_behavior', {}).get('findings', [])
            if code_findings:
                high_risk_findings = [f for f in code_findings if f.get('severity') in ['high', 'critical']]
                if high_risk_findings:
                    analysis.append(f"Code analysis detected {len(high_risk_findings)} high-risk patterns including obfuscation, dangerous API usage, or potential injection vulnerabilities.")
        elif scores['code_behavior'] < 3:
            analysis.append("Code analysis shows clean patterns with no suspicious behavior detected. The codebase appears to follow security best practices.")
        
        # Analyze network behavior
        if scores['network'] > 7:
            network_data = all_results.get('network', {}).get('data', {})
            if network_data.get('http_urls', 0) > 0:
                analysis.append("The extension makes insecure HTTP requests which could expose sensitive data to interception or tampering.")
            if network_data.get('tracking_domains', 0) > 0:
                analysis.append("The extension communicates with known tracking or analytics domains, which may compromise user privacy.")
        elif scores['network'] < 3:
            analysis.append("The extension shows minimal network activity and uses secure communication protocols, indicating good privacy practices.")
        
        # Analyze threat intelligence
        if scores['threat_intel'] > 7:
            analysis.append("Threat intelligence sources have identified potential security concerns with this extension's network endpoints or behavior patterns.")
        
        return analysis
    
    def _generate_attack_scenarios(self, all_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate potential attack scenarios"""
        scenarios = []
        
        # Data exfiltration scenario
        network_data = all_results.get('network', {}).get('data', {})
        if network_data.get('external_urls', 0) > 0:
            scenarios.append({
                'title': 'Data Exfiltration',
                'description': 'The extension could potentially exfiltrate sensitive user data to external servers. This includes browsing history, personal information, or credentials.',
                'likelihood': 'High' if network_data.get('http_urls', 0) > 0 else 'Medium',
                'impact': 'High'
            })
        
        # Code injection scenario
        code_data = all_results.get('code_behavior', {}).get('data', {})
        if code_data.get('total_patterns_found', 0) > 0:
            scenarios.append({
                'title': 'Code Injection',
                'description': 'The extension may be vulnerable to or capable of code injection attacks, potentially allowing execution of arbitrary JavaScript on web pages.',
                'likelihood': 'Medium',
                'impact': 'High'
            })
        
        # Privacy violation scenario
        if all_results.get('permissions', {}).get('score', 0) > 6:
            scenarios.append({
                'title': 'Privacy Violation',
                'description': 'With the requested permissions, the extension could access and collect sensitive user data including browsing history, cookies, and personal information.',
                'likelihood': 'High',
                'impact': 'Medium'
            })
        
        # Malware distribution scenario
        if all_results.get('threat_intel', {}).get('score', 0) > 6:
            scenarios.append({
                'title': 'Malware Distribution',
                'description': 'The extension may be involved in malware distribution or communicate with malicious command and control servers.',
                'likelihood': 'Medium',
                'impact': 'Critical'
            })
        
        return scenarios
    
    def _generate_recommendations(self, weighted_score: float, all_results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Get recommendations based on risk level
        risk_level = self._get_risk_level(weighted_score)
        base_recommendations = self.risk_categories.get(risk_level, {}).get('recommendations', [])
        recommendations.extend(base_recommendations)
        
        # Specific recommendations based on findings
        if all_results.get('permissions', {}).get('score', 0) > 7:
            recommendations.append("Review and justify each requested permission. Consider if the extension's functionality truly requires such extensive access.")
        
        if all_results.get('code_behavior', {}).get('score', 0) > 6:
            recommendations.append("Investigate the detected code patterns. Consider using static analysis tools for deeper inspection of the codebase.")
        
        if all_results.get('network', {}).get('data', {}).get('http_urls', 0) > 0:
            recommendations.append("Require the developer to use HTTPS for all network communications to protect data in transit.")
        
        if all_results.get('network', {}).get('data', {}).get('tracking_domains', 0) > 0:
            recommendations.append("Evaluate the privacy implications of the tracking domains. Consider implementing additional privacy controls.")
        
        # Add implementation-specific recommendations
        recommendations.append("Implement runtime monitoring to detect any unexpected behavior from the extension.")
        recommendations.append("Regularly review and update the extension's security posture as new versions are released.")
        
        return recommendations
    
    def _generate_summary(self, weighted_score: float, all_results: Dict[str, Any]) -> str:
        """Generate executive summary"""
        risk_level = self._get_risk_level(weighted_score)
        risk_info = self.risk_categories.get(risk_level, {})
        
        summary = f"This extension has been analyzed and assigned a risk score of {weighted_score:.1f}/10, "
        summary += f"classifying it as {risk_level.upper()} risk. {risk_info.get('description', 'Unknown risk level')}. "
        
        # Add key findings
        key_findings = []
        
        if all_results.get('permissions', {}).get('score', 0) > 7:
            key_findings.append("requests extensive permissions")
        
        if all_results.get('code_behavior', {}).get('score', 0) > 6:
            key_findings.append("contains suspicious code patterns")
        
        if all_results.get('network', {}).get('data', {}).get('http_urls', 0) > 0:
            key_findings.append("uses insecure communications")
        
        if all_results.get('threat_intel', {}).get('score', 0) > 6:
            key_findings.append("has threat intelligence indicators")
        
        if key_findings:
            summary += f"Key security concerns include: {', '.join(key_findings)}. "
        
        summary += "A detailed breakdown of the analysis is provided in the sections below."
        
        return summary
    
    def _generate_explanations(self, scores: Dict[str, float], all_results: Dict[str, Any]) -> List[str]:
        """Generate detailed explanations"""
        explanations = []
        
        # Permission explanations
        if scores['permissions'] <= 3:
            explanations.append("The extension requests minimal permissions, reducing its potential attack surface and limiting access to sensitive user data.")
        elif scores['permissions'] >= 7:
            explanations.append("The extension requests extensive permissions that could provide access to sensitive user data, browsing history, or system resources.")
        
        # Code behavior explanations
        if scores['code_behavior'] <= 3:
            explanations.append("Static code analysis reveals clean programming patterns with no indicators of obfuscation, injection vulnerabilities, or malicious behavior.")
        elif scores['code_behavior'] >= 7:
            explanations.append("Code analysis detected multiple suspicious patterns including potential obfuscation, dangerous API usage, or injection attack vectors.")
        
        # Network explanations
        if scores['network'] <= 3:
            explanations.append("Network analysis shows the extension communicates with a limited number of external domains using secure protocols, indicating good privacy practices.")
        elif scores['network'] >= 7:
            explanations.append("The extension makes extensive external network connections, some of which may be insecure or involve tracking services, potentially compromising user privacy.")
        
        return explanations
    
    def _get_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score <= 3:
            return 'low'
        elif score <= 6:
            return 'medium'
        elif score <= 8:
            return 'high'
        else:
            return 'critical'

# Export the analyzer
__all__ = ['AIAnalyzer']