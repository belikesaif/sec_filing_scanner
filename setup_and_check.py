#!/usr/bin/env python3
"""
SEC Filing Scanner - Comprehensive Setup and Dependency Checker
This script checks all dependencies, fixes common issues, and sets up the environment.
"""

import os
import sys
import subprocess
import importlib
import pkg_resources
import platform
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json

class Colors:
    """Terminal colors for better output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class DependencyManager:
    """Manages dependency checking, installation, and validation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.results = {
            "system_info": {},
            "missing_packages": [],
            "conflicting_packages": [],
            "outdated_packages": [],
            "installation_errors": [],
            "import_errors": [],
            "environment_issues": []
        }
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")
        
    def print_status(self, message: str, status: str = "info"):
        """Print a status message with color coding"""
        color_map = {
            "success": Colors.GREEN,
            "error": Colors.RED,
            "warning": Colors.YELLOW,
            "info": Colors.BLUE
        }
        color = color_map.get(status, Colors.WHITE)
        print(f"{color}[{status.upper()}] {message}{Colors.END}")
        
    def get_system_info(self):
        """Collect system information"""
        info = {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "pip_version": None,
            "virtualenv": None
        }
        
        # Check pip version
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info["pip_version"] = result.stdout.strip()
        except Exception as e:
            self.print_status(f"Could not get pip version: {e}", "warning")
            
        # Check if in virtual environment
        info["virtualenv"] = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        self.results["system_info"] = info
        return info
        
    def display_system_info(self):
        """Display system information"""
        self.print_header("SYSTEM INFORMATION")
        info = self.get_system_info()
        
        print(f"Python Version: {info['python_version'].split()[0]}")
        print(f"Python Executable: {info['python_executable']}")
        print(f"Platform: {info['platform']}")
        print(f"Architecture: {info['architecture'][0]}")
        if info["pip_version"]:
            print(f"Pip Version: {info['pip_version']}")
        print(f"Virtual Environment: {'Yes' if info['virtualenv'] else 'No'}")
        
        if not info["virtualenv"]:
            self.print_status("WARNING: Not running in a virtual environment!", "warning")
            self.print_status("Consider creating a virtual environment:", "info")
            self.print_status("python -m venv venv", "info")
            self.print_status("venv\\Scripts\\activate  # Windows", "info")
            self.print_status("source venv/bin/activate  # Linux/Mac", "info")
            
    def read_requirements(self) -> List[str]:
        """Read and parse requirements.txt"""
        if not self.requirements_file.exists():
            self.print_status(f"Requirements file not found: {self.requirements_file}", "error")
            return []
            
        try:
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Filter out comments and empty lines
            requirements = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    requirements.append(line)
                    
            return requirements
        except Exception as e:
            self.print_status(f"Error reading requirements.txt: {e}", "error")
            return []
            
    def validate_requirements_format(self, requirements: List[str]) -> List[str]:
        """Validate and fix requirements format"""
        self.print_header("VALIDATING REQUIREMENTS FORMAT")
        
        fixed_requirements = []
        issues_found = False
        
        for req in requirements:
            original_req = req
            
            # Check for missing version specifiers
            if req and '==' not in req and '>=' not in req and '<=' not in req and '~=' not in req and '>' not in req and '<' not in req:
                self.print_status(f"No version specified for: {req}", "warning")
                issues_found = True
                
            # Fix common issues
            req = req.replace(' ', '')  # Remove spaces
            
            # Validate package name format
            if req and not req[0].isalpha() and req[0] != '_':
                self.print_status(f"Invalid package name format: {req}", "error")
                continue
                
            if req:
                fixed_requirements.append(req)
                
        if issues_found:
            self.print_status("Consider specifying exact versions for better reproducibility", "warning")
            
        return fixed_requirements
        
    def check_installed_packages(self) -> Dict[str, str]:
        """Get list of installed packages"""
        try:
            installed = {}
            for dist in pkg_resources.working_set:
                installed[dist.project_name.lower()] = dist.version
            return installed
        except Exception as e:
            self.print_status(f"Error getting installed packages: {e}", "error")
            return {}
            
    def parse_requirement(self, req: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Parse a requirement string into package name, operator, and version"""
        import re
        
        # Pattern to match package[extras]==version or package>=version etc.
        pattern = r'^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?\s*([><=!~]+)?\s*([0-9.]+.*)?$'
        match = re.match(pattern, req.strip())
        
        if match:
            package, operator, version = match.groups()
            return package.lower(), operator, version
        else:
            # Fallback for simple package names
            return req.strip().lower(), None, None
            
    def check_dependencies(self, requirements: List[str]):
        """Check if all dependencies are installed and compatible"""
        self.print_header("CHECKING DEPENDENCIES")
        
        installed = self.check_installed_packages()
        missing = []
        conflicting = []
        
        for req in requirements:
            package, operator, version = self.parse_requirement(req)
            
            if package in installed:
                installed_version = installed[package]
                if operator and version:
                    # Check version compatibility
                    try:
                        if operator == "==" and installed_version != version:
                            conflicting.append((package, installed_version, f"{operator}{version}"))
                        elif operator == ">=" and not self._version_satisfies(installed_version, version, ">="):
                            conflicting.append((package, installed_version, f"{operator}{version}"))
                        # Add more version checks as needed
                    except Exception:
                        pass
                        
                self.print_status(f"✓ {package} ({installed_version})", "success")
            else:
                missing.append(req)
                self.print_status(f"✗ {package} - NOT INSTALLED", "error")
                
        self.results["missing_packages"] = missing
        self.results["conflicting_packages"] = conflicting
        
        return missing, conflicting
        
    def _version_satisfies(self, installed: str, required: str, operator: str) -> bool:
        """Check if installed version satisfies requirement"""
        try:
            from packaging import version
            inst_ver = version.parse(installed)
            req_ver = version.parse(required)
            
            if operator == ">=":
                return inst_ver >= req_ver
            elif operator == "<=":
                return inst_ver <= req_ver
            elif operator == ">":
                return inst_ver > req_ver
            elif operator == "<":
                return inst_ver < req_ver
            elif operator == "==":
                return inst_ver == req_ver
            elif operator == "!=":
                return inst_ver != req_ver
        except:
            return True  # If we can't parse, assume it's OK
            
        return True
        
    def install_missing_packages(self, missing: List[str], force: bool = False):
        """Install missing packages"""
        if not missing and not force:
            self.print_status("No missing packages to install", "success")
            return
            
        self.print_header("INSTALLING MISSING PACKAGES")
        
        # Upgrade pip first
        self.print_status("Upgrading pip...", "info")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            self.print_status("Pip upgraded successfully", "success")
        except subprocess.CalledProcessError as e:
            self.print_status(f"Warning: Could not upgrade pip: {e}", "warning")
            
        # Install packages
        for package in missing:
            self.print_status(f"Installing {package}...", "info")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    capture_output=True,
                    text=True
                )
                self.print_status(f"✓ Successfully installed {package}", "success")
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to install {package}: {e.stderr}"
                self.print_status(error_msg, "error")
                self.results["installation_errors"].append((package, error_msg))
                
    def test_imports(self):
        """Test importing key packages"""
        self.print_header("TESTING IMPORTS")
        
        # Key packages used in the project
        test_packages = [
            ('streamlit', 'streamlit'),
            ('fastapi', 'fastapi'),
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('plotly', 'plotly.express'),
            ('openai', 'openai'),
            ('chromadb', 'chromadb'),
            ('beautifulsoup4', 'bs4'),
            ('langchain', 'langchain'),
            ('torch', 'torch'),
            ('transformers', 'transformers'),
            ('scikit-learn', 'sklearn'),
            ('requests', 'requests'),
            ('sqlalchemy', 'sqlalchemy'),
            ('python-dotenv', 'dotenv'),
            ('uvicorn', 'uvicorn'),
        ]
        
        import_errors = []
        
        for package_name, import_name in test_packages:
            try:
                importlib.import_module(import_name)
                self.print_status(f"✓ {package_name}", "success")
            except ImportError as e:
                error_msg = f"Cannot import {package_name}: {e}"
                self.print_status(f"✗ {error_msg}", "error")
                import_errors.append((package_name, str(e)))
            except Exception as e:
                error_msg = f"Unexpected error importing {package_name}: {e}"
                self.print_status(f"✗ {error_msg}", "error")
                import_errors.append((package_name, str(e)))
                
        self.results["import_errors"] = import_errors
        return import_errors
        
    def check_environment_variables(self):
        """Check required environment variables"""
        self.print_header("CHECKING ENVIRONMENT VARIABLES")
        
        required_vars = [
            "OPENAI_API_KEY",
            "SEC_EMAIL"
        ]
        
        optional_vars = [
            "FILINGS_DIR",
            "DATABASE_URL"
        ]
        
        missing_required = []
        
        for var in required_vars:
            if os.getenv(var):
                self.print_status(f"✓ {var} is set", "success")
            else:
                self.print_status(f"✗ {var} is missing", "error")
                missing_required.append(var)
                
        for var in optional_vars:
            if os.getenv(var):
                self.print_status(f"✓ {var} is set", "info")
            else:
                self.print_status(f"- {var} is not set (optional)", "warning")
                
        if missing_required:
            self.print_status("\nCreate a .env file with required variables:", "info")
            print("Example .env file content:")
            print("OPENAI_API_KEY=your_openai_api_key_here")
            print("SEC_EMAIL=your_email@example.com")
            
        self.results["environment_issues"] = missing_required
        return missing_required
        
    def check_project_structure(self):
        """Check if project structure is correct"""
        self.print_header("CHECKING PROJECT STRUCTURE")
        
        required_dirs = [
            "app",
            "app/services",
            "app/core",
            "app/models",
            "app/utils",
            "scripts",
            "tests"
        ]
        
        required_files = [
            "app/__init__.py",
            "app/main.py",
            "streamlit_app.py",
            "requirements.txt"
        ]
        
        missing_items = []
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                self.print_status(f"✓ {dir_path}/", "success")
            else:
                self.print_status(f"✗ {dir_path}/ - missing", "error")
                missing_items.append(dir_path)
                
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.print_status(f"✓ {file_path}", "success")
            else:
                self.print_status(f"✗ {file_path} - missing", "error")
                missing_items.append(file_path)
                
        return missing_items
        
    def create_fixed_requirements(self):
        """Create a fixed requirements.txt file"""
        self.print_header("CREATING FIXED REQUIREMENTS.TXT")
        
        # Enhanced requirements with proper versions
        fixed_requirements = [
            "# Core Framework Dependencies",
            "fastapi==0.115.11",
            "uvicorn==0.34.0",
            "streamlit==1.35.0",
            "",
            "# Data Processing and Analysis",
            "pandas==2.2.2",
            "numpy==1.26.4",
            "plotly==5.22.0",
            "",
            "# AI and Machine Learning",
            "openai==1.66.3",
            "langchain==0.3.20",
            "langchain-chroma==0.2.2",
            "langchain-core==0.3.45",
            "langchain-huggingface==0.1.2",
            "langchain-openai==0.3.8",
            "langchain-text-splitters==0.3.6",
            "langgraph==0.3.10",
            "langgraph-checkpoint==2.0.19",
            "langgraph-prebuilt==0.1.3",
            "langgraph-sdk==0.1.57",
            "langsmith==0.3.13",
            "",
            "# Vector Database and Embeddings",
            "chromadb==0.6.3",
            "chroma-hnswlib==0.7.6",
            "sentence-transformers==3.4.1",
            "",
            "# Deep Learning",
            "torch==2.6.0",
            "transformers==4.49.0",
            "tokenizers==0.21.1",
            "safetensors==0.5.3",
            "huggingface-hub==0.29.3",
            "",
            "# Traditional ML",
            "scikit-learn==1.6.1",
            "scipy==1.13.0",
            "",
            "# Web Scraping and Processing",
            "beautifulsoup4==4.13.3",
            "requests==2.32.3",
            "sec-edgar-downloader==5.0.3",
            "",
            "# Database",
            "sqlalchemy==2.0.39",
            "alembic==1.13.1",
            "",
            "# Utilities",
            "python-dotenv==1.0.1",
            "click==8.1.8",
            "typer==0.15.2",
            "pydantic==2.10.6",
            "pydantic-core==2.27.2",
            "",
            "# Development and Testing",
            "pytest==8.2.1",
            "pytest-cov==5.0.0",
            "",
            "# Networking and HTTP",
            "httpx==0.28.1",
            "httpcore==1.0.7",
            "anyio==4.8.0",
            "",
            "# Other Dependencies",
            "packaging==24.2",
            "python-dateutil==2.9.0.post0",
            "regex==2024.11.6",
            "tiktoken==0.9.0",
            "tqdm==4.67.1",
            "rich==13.9.4",
            "coloredlogs==15.0.1",
            "",
            "# Supporting Libraries",
            "annotated-types==0.7.0",
            "asgiref==3.8.1",
            "backoff==2.2.1",
            "bcrypt==4.3.0",
            "build==1.2.2.post1",
            "cachetools==5.5.2",
            "certifi==2025.1.31",
            "charset-normalizer==3.4.1",
            "Deprecated==1.2.18",
            "distro==1.9.0",
            "durationpy==0.9",
            "filelock==3.18.0",
            "flatbuffers==25.2.10",
            "fsspec==2025.3.0",
            "google-auth==2.38.0",
            "googleapis-common-protos==1.69.1",
            "grpcio==1.71.0",
            "h11==0.14.0",
            "httptools==0.6.4",
            "humanfriendly==10.0",
            "idna==3.10",
            "importlib-metadata==8.6.1",
            "importlib-resources==6.5.2",
            "Jinja2==3.1.6",
            "jiter==0.9.0",
            "joblib==1.4.2",
            "jsonpatch==1.33",
            "jsonpointer==3.0.0",
            "kubernetes==32.0.1",
            "markdown-it-py==3.0.0",
            "MarkupSafe==3.0.2",
            "mdurl==0.1.2",
            "mmh3==5.1.0",
            "monotonic==1.6",
            "mpmath==1.3.0",
            "msgpack==1.1.0",
            "networkx==3.3",
            "oauthlib==3.2.2",
            "onnxruntime==1.18.0",
            "opentelemetry-api==1.31.0",
            "opentelemetry-exporter-otlp-proto-common==1.31.0",
            "opentelemetry-exporter-otlp-proto-grpc==1.31.0",
            "opentelemetry-instrumentation==0.52b0",
            "opentelemetry-instrumentation-asgi==0.52b0",
            "opentelemetry-instrumentation-fastapi==0.52b0",
            "opentelemetry-proto==1.31.0",
            "opentelemetry-sdk==1.31.0",
            "opentelemetry-semantic-conventions==0.52b0",
            "opentelemetry-util-http==0.52b0",
            "orjson==3.10.15",
            "overrides==7.7.0",
            "pillow==11.1.0",
            "posthog==3.20.0",
            "protobuf==5.29.3",
            "pyasn1==0.6.1",
            "pyasn1-modules==0.4.1",
            "Pygments==2.19.1",
            "PyPika==0.48.9",
            "pyproject-hooks==1.2.0",
            "pyrate-limiter==3.7.0",
            "PyYAML==6.0.2",
            "requests-oauthlib==2.0.0",
            "requests-toolbelt==1.0.0",
            "rsa==4.9",
            "shellingham==1.5.4",
            "six==1.17.0",
            "sniffio==1.3.1",
            "soupsieve==2.6",
            "starlette==0.46.1",
            "sympy==1.13.1",
            "tenacity==9.0.0",
            "threadpoolctl==3.6.0",
            "typing-extensions==4.12.2",
            "urllib3==2.3.0",
            "uvloop==0.21.0",
            "watchfiles==1.0.4",
            "websocket-client==1.8.0",
            "websockets==15.0.1",
            "wrapt==1.17.2",
            "zipp==3.21.0",
            "zstandard==0.23.0"
        ]
        
        # Backup original file
        if self.requirements_file.exists():
            backup_file = self.requirements_file.with_suffix('.txt.backup')
            import shutil
            shutil.copy2(self.requirements_file, backup_file)
            self.print_status(f"Backed up original requirements.txt to {backup_file}", "info")
            
        # Write fixed requirements
        with open(self.requirements_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_requirements))
            
        self.print_status(f"Created fixed requirements.txt with {len([r for r in fixed_requirements if r and not r.startswith('#')])} packages", "success")
        
    def run_comprehensive_check(self, install_missing: bool = False, fix_requirements: bool = False):
        """Run all checks and fixes"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}SEC Filing Scanner - Comprehensive Setup{Colors.END}")
        print(f"{Colors.MAGENTA}Starting comprehensive dependency check...{Colors.END}\n")
        
        # System info
        self.display_system_info()
        
        # Check project structure
        missing_structure = self.check_project_structure()
        
        # Read and validate requirements
        requirements = self.read_requirements()
        if fix_requirements or not requirements:
            self.create_fixed_requirements()
            requirements = self.read_requirements()
            
        fixed_requirements = self.validate_requirements_format(requirements)
        
        # Check dependencies
        missing, conflicting = self.check_dependencies(fixed_requirements)
        
        # Install missing packages if requested
        if install_missing and missing:
            self.install_missing_packages(missing)
            # Re-check after installation
            missing, conflicting = self.check_dependencies(fixed_requirements)
            
        # Test imports
        import_errors = self.test_imports()
        
        # Check environment variables
        env_errors = self.check_environment_variables()
        
        # Summary
        self.print_summary()
        
        return self.results
        
    def print_summary(self):
        """Print a summary of all results"""
        self.print_header("SUMMARY")
        
        total_issues = (len(self.results["missing_packages"]) + 
                       len(self.results["conflicting_packages"]) + 
                       len(self.results["installation_errors"]) + 
                       len(self.results["import_errors"]) + 
                       len(self.results["environment_issues"]))
        
        if total_issues == 0:
            self.print_status("🎉 All checks passed! Your environment is ready.", "success")
        else:
            self.print_status(f"⚠️  Found {total_issues} issues that need attention:", "warning")
            
            if self.results["missing_packages"]:
                print(f"\n  Missing packages ({len(self.results['missing_packages'])}):")
                for pkg in self.results["missing_packages"]:
                    print(f"    - {pkg}")
                    
            if self.results["conflicting_packages"]:
                print(f"\n  Version conflicts ({len(self.results['conflicting_packages'])}):")
                for pkg, installed, required in self.results["conflicting_packages"]:
                    print(f"    - {pkg}: installed {installed}, required {required}")
                    
            if self.results["import_errors"]:
                print(f"\n  Import errors ({len(self.results['import_errors'])}):")
                for pkg, error in self.results["import_errors"]:
                    print(f"    - {pkg}: {error}")
                    
            if self.results["environment_issues"]:
                print(f"\n  Missing environment variables ({len(self.results['environment_issues'])}):")
                for var in self.results["environment_issues"]:
                    print(f"    - {var}")
                    
        print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
        if self.results["missing_packages"]:
            print("1. Install missing packages: python setup_and_check.py --install")
        if self.results["environment_issues"]:
            print("2. Create .env file with required environment variables")
        print("3. Run the application: streamlit run streamlit_app.py")
        print("4. Or start the API: python -m app.main")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SEC Filing Scanner Setup and Dependency Checker")
    parser.add_argument("--install", action="store_true", help="Automatically install missing packages")
    parser.add_argument("--fix-requirements", action="store_true", help="Create a fixed requirements.txt file")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    manager = DependencyManager()
    results = manager.run_comprehensive_check(
        install_missing=args.install,
        fix_requirements=args.fix_requirements
    )
    
    if args.json:
        print(json.dumps(results, indent=2))
    
    # Exit with error code if there are issues
    total_issues = (len(results["missing_packages"]) + 
                   len(results["conflicting_packages"]) + 
                   len(results["installation_errors"]) + 
                   len(results["import_errors"]) + 
                   len(results["environment_issues"]))
    
    sys.exit(1 if total_issues > 0 else 0)

if __name__ == "__main__":
    main()
