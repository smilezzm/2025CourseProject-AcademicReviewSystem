"""
Security validation module for input sanitization and injection protection.
"""

import re
import html
from typing import Dict, Any, Union
from urllib.parse import urlparse


class SecurityValidator:
    """Comprehensive security validator for user inputs"""
    
    def __init__(self):
        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|TRUNCATE|GRANT|REVOKE)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"('\s*(OR|AND)\s*')",
            r"(\bunion\s+select\b)",
            r"(\binto\s+outfile\b)",
            r"(\bload_file\b)",
        ]
        
        # Command injection patterns  
        self.cmd_patterns = [
            r"(\b(system|exec|eval|shell_exec|passthru|popen|proc_open|subprocess|os\.system)\b)",
            r"(&&|\|\||;|`|\$\(|\${)",
            r"(\b(rm|del|format|shutdown|reboot|kill|killall|pkill)\b)",
            r"(\.\.\/|\.\.\\|\/etc\/|\/bin\/|\/usr\/|\/var\/)",
            r"(\b(curl|wget|nc|netcat|telnet|ssh|ftp)\b)",
            r"(\b(chmod|chown|chgrp|sudo|su)\b)",
        ]
        
        # Script injection patterns
        self.script_patterns = [
            r"(<script[^>]*>.*?</script>)",
            r"(javascript:|vbscript:|data:text\/html)",
            r"(on\w+\s*=)",
            r"(<iframe|<object|<embed|<form|<input)",
            r"(expression\s*\(|@import|url\s*\()",
            r"(<svg[^>]*>.*?</svg>)",
        ]
        
        # Python code injection patterns
        self.python_patterns = [
            r"(\b(__import__|getattr|setattr|delattr|hasattr|callable|compile|eval|exec)\b)",
            r"(\b(globals|locals|vars|dir|input|raw_input)\b)",
            r"(\b(open|file|execfile|reload|__builtins__)\b)",
            r"(\b(os\.|sys\.|subprocess\.|pickle\.|marshal\.)\b)",
        ]
        
        # Common malicious keywords
        self.blacklist = [
            "system", "sudo", "rm -rf", "drop table", "exec", "eval",
            "shell", "cmd", "powershell", "bash", "chmod", "chown",
            "__import__", "getattr", "setattr", "delattr", "subprocess",
            "os.system", "sys.exit", "pickle.loads", "marshal.loads",
            "input()", "raw_input()", "file(", "open(", "execfile",
            "<script", "javascript:", "vbscript:", "onload=", "onerror=",
            "document.cookie", "window.location", "eval(", "setTimeout",
            "setInterval", "innerHTML", "outerHTML", "insertAdjacentHTML"
        ]
    
    def validate_domain_input(self, domain: str, years: str, paper_count: int, temperature: float) -> Dict[str, Any]:
        """Validate and sanitize domain input parameters"""
        
        # Validate domain
        if not isinstance(domain, str):
            raise ValueError("Domain must be a string")
        
        domain = self._sanitize_text_input(domain, max_length=100)
        
        if len(domain.strip()) < 2:
            raise ValueError("Domain must be at least 2 characters long")
        
        # Validate domain format - only allow letters, numbers, spaces, hyphens, and common academic terms
        if not re.match(r'^[\w\s\-\.\(\)\+\&\/]+$', domain):
            raise ValueError("Domain contains invalid characters. Only letters, numbers, spaces, hyphens, dots, and parentheses are allowed")
        
        # Validate years
        if not isinstance(years, str):
            raise ValueError("Years must be a string in format 'YYYY-YYYY'")
        
        years = self._sanitize_text_input(years, max_length=20)
        
        if not re.match(r'^\d{4}-\d{4}$', years):
            raise ValueError("Years must be in format 'YYYY-YYYY'")
        
        year_start, year_end = map(int, years.split('-'))
        current_year = 2025  # Update as needed
        
        if year_start < 1990 or year_end > current_year:
            raise ValueError(f"Years must be between 1990 and {current_year}")
        
        if year_start > year_end:
            raise ValueError("Start year must be less than or equal to end year")
        
        # Validate paper count
        if not isinstance(paper_count, (int, float)):
            raise ValueError("Paper count must be a number")
        
        paper_count = int(paper_count)
        
        if paper_count < 1 or paper_count > 50:
            raise ValueError("Paper count must be between 1 and 50")
        
        # Validate temperature
        if not isinstance(temperature, (int, float)):
            raise ValueError("Temperature must be a number")
        
        temperature = float(temperature)
        
        if temperature < 0.1 or temperature > 2.0:
            raise ValueError("Temperature must be between 0.1 and 2.0")
        
        return {
            'domain': domain,
            'years': years,
            'paper_count': paper_count,
            'temperature': temperature
        }
    
    def _sanitize_text_input(self, text: str, max_length: int = 1000) -> str:
        """Comprehensive text input sanitization"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        # Check for injection patterns
        self._check_injection_patterns(text)
        
        # HTML encode dangerous characters
        text = html.escape(text, quote=True)
        
        # Remove null bytes and other dangerous characters
        text = text.replace('\x00', '').replace('\r', '').replace('\n', ' ')
        
        # Limit length
        if len(text) > max_length:
            raise ValueError(f"Input too long. Maximum {max_length} characters allowed")
        
        return text.strip()
    
    def _check_injection_patterns(self, text: str) -> None:
        """Check text against all injection patterns"""
        text_lower = text.lower()
        
        # Check SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError(f"Potentially malicious SQL pattern detected")
        
        # Check command injection patterns
        for pattern in self.cmd_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError(f"Potentially malicious command pattern detected")
        
        # Check script injection patterns
        for pattern in self.script_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError(f"Potentially malicious script pattern detected")
        
        # Check Python code injection patterns
        for pattern in self.python_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise ValueError(f"Potentially malicious Python code pattern detected")
        
        # Check blacklist
        for word in self.blacklist:
            if word.lower() in text_lower:
                raise ValueError(f"Blocked keyword detected: {word}")
    
    def sanitize_output(self, text: str) -> str:
        """Sanitize output text to prevent XSS and other attacks"""
        if not isinstance(text, str):
            return str(text)
        
        # Basic HTML escaping for safety
        text = html.escape(text, quote=False)
        
        # Remove potentially dangerous script tags and attributes
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        text = re.sub(r'javascript:[^"\'>\s]*', '', text, flags=re.IGNORECASE)
        
        return text
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is safe and well-formed"""
        if not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url)
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for valid hostname
            if not parsed.netloc:
                return False
            
            # Block local/private URLs
            if any(parsed.netloc.startswith(prefix) for prefix in 
                   ['localhost', '127.', '192.168.', '10.', '172.']):
                return False
            
            # Block file:// and other dangerous schemes
            if parsed.scheme in ['file', 'ftp', 'javascript', 'data']:
                return False
            
            return True
            
        except Exception:
            return False


# Global instance
security_validator = SecurityValidator()
