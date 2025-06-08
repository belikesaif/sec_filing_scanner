#!/usr/bin/env python3
"""
SEC Filing Scanner - Comprehensive Multi-Setup Script
This script performs complete environment setup, dependency resolution, and validation
Only proceeds to build when ALL requirements are satisfied
"""

import os
import sys
import subprocess
import importlib
import platform
import json
import time
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import tempfile
import pkg_resources

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

class ComprehensiveSetup:
    """Complete setup manager for SEC Filing Scanner"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.fixed_requirements_file = self.project_root / "requirements_fixed.txt"
        self.venv_path = self.project_root / ".venv"
        
        self.results = {
            "system_info": {},
            "setup_phases": [],
            "errors": [],
            "warnings": [],
            "success_steps": []
        }
        
    def print_header(self, text: str, color=Colors.CYAN):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{color}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{color}{text.center(80)}{Colors.END}")
        print(f"{Colors.BOLD}{color}{'='*80}{Colors.END}\n")
        
    def print_step(self, text: str, status: str = "INFO"):
        """Print a step with appropriate color"""
        colors = {
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "INFO": Colors.BLUE
        }
        symbol = {
            "SUCCESS": "✓",
            "ERROR": "✗",
            "WARNING": "⚠",
            "INFO": "→"
        }
        color = colors.get(status, Colors.WHITE)
        sym = symbol.get(status, "•")
        print(f"{color}[{status}]{Colors.END} {sym} {text}")
        
    def run_command(self, command: List[str], description: str = "", timeout: int = 300) -> Tuple[bool, str, str]:
        """Run a command and return success, stdout, stderr"""
        try:
            if description:
                self.print_step(f"Running: {description}", "INFO")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return True, result.stdout, result.stderr
            else:
                return False, result.stdout, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def check_system_requirements(self) -> bool:
        """Check system requirements and Python version"""
        self.print_header("PHASE 1: SYSTEM REQUIREMENTS CHECK")
        
        # Check Python version
        python_version = sys.version_info
        self.print_step(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}", "INFO")
        
        if python_version < (3, 8):
            self.print_step("Python 3.8+ is required!", "ERROR")
            return False
        elif python_version >= (3, 12):
            self.print_step("Python 3.12+ detected - some packages may have compatibility issues", "WARNING")
            
        self.print_step("Python version check passed", "SUCCESS")
        
        # Check pip
        try:
            import pip
            self.print_step(f"Pip is available: {pip.__version__}", "SUCCESS")
        except ImportError:
            self.print_step("Pip is not available", "ERROR")
            return False
            
        # Check platform
        self.print_step(f"Platform: {platform.system()} {platform.release()}", "INFO")
        
        # Check virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.print_step("Virtual environment detected", "SUCCESS")
        else:
            self.print_step("No virtual environment detected - this is recommended but not required", "WARNING")
            
        return True
    
    def create_fixed_requirements(self) -> bool:
        """Create a fixed requirements.txt with compatible versions"""
        self.print_header("PHASE 2: REQUIREMENTS ANALYSIS AND FIXING")
        
        # Updated requirements with compatible versions for Python 3.13
        fixed_requirements = """# Core framework dependencies
fastapi==0.115.11
uvicorn[standard]==0.34.0
python-dotenv==1.0.1
pydantic==2.10.6
pydantic-core==2.27.2

# Database and storage
SQLAlchemy==2.0.39
sqlite3  # Built-in

# SEC filing downloading
sec-edgar-downloader==5.0.3

# Web scraping and parsing
beautifulsoup4==4.13.3
requests==2.32.3
requests-oauthlib==2.0.0
requests-toolbelt==1.0.0

# Vector database and embeddings
chromadb==0.6.3
chroma-hnswlib==0.7.6

# OpenAI and AI/ML
openai==1.66.3
tiktoken==0.9.0

# LangChain ecosystem - compatible versions
langchain==0.3.20
langchain-core==0.3.45
langchain-openai==0.3.8
langchain-chroma==0.2.2
langchain-huggingface==0.1.2
langchain-text-splitters==0.3.6
langgraph==0.3.10
langgraph-checkpoint==2.0.19
langgraph-prebuilt==0.1.3
langgraph-sdk==0.1.57
langsmith==0.3.13

# Machine learning and data science
torch==2.6.0
transformers==4.49.0
sentence-transformers==3.4.1
scikit-learn==1.6.1
numpy==1.26.4
pandas==2.2.2

# Streamlit and visualization
streamlit==1.35.0
plotly==5.22.0

# Scientific computing
scipy==1.13.0
networkx==3.3
onnxruntime==1.18.0

# Utilities and helpers
typer==0.15.2
click==8.1.8
rich==13.9.4
coloredlogs==15.0.1
tqdm==4.67.1

# Testing
pytest==8.2.1
pytest-cov==5.0.0

# Database migrations
alembic==1.13.1

# Development tools
jupyter==1.0.0

# HTTP and networking
httpx==0.28.1
httpcore==1.0.7
httptools==0.6.4
h11==0.14.0
anyio==4.8.0
sniffio==1.3.1

# Async and concurrency
uvloop==0.21.0; sys_platform != "win32"
watchfiles==1.0.4
websockets==15.0.1
websocket-client==1.8.0

# Serialization and data formats
orjson==3.10.15
msgpack==1.1.0
PyYAML==6.0.2
toml

# Authentication and security
bcrypt==4.3.0
oauthlib==3.2.2

# Google Cloud and monitoring
google-auth==2.38.0
googleapis-common-protos==1.69.1
grpcio==1.71.0

# OpenTelemetry (monitoring)
opentelemetry-api==1.31.0
opentelemetry-sdk==1.31.0
opentelemetry-exporter-otlp-proto-grpc==1.31.0
opentelemetry-exporter-otlp-proto-common==1.31.0
opentelemetry-instrumentation==0.52b0
opentelemetry-instrumentation-fastapi==0.52b0
opentelemetry-instrumentation-asgi==0.52b0
opentelemetry-proto==1.31.0
opentelemetry-semantic-conventions==0.52b0
opentelemetry-util-http==0.52b0

# Template and markup
Jinja2==3.1.6
MarkupSafe==3.0.2
markdown-it-py==3.0.0
mdurl==0.1.2

# Progress and rate limiting
pyrate-limiter==3.7.0
backoff==2.2.1

# Caching and storage
cachetools==5.5.2
diskcache

# File and path utilities
pathlib2; python_version < "3.4"
filelock==3.18.0
fsspec==2025.3.0

# Low level utilities
six==1.17.0
wrapt==1.17.2
typing-extensions==4.12.2
importlib-metadata==8.6.1; python_version < "3.8"
importlib-resources==6.5.2; python_version < "3.9"
zipp==3.21.0

# Compression
zstandard==0.23.0

# Image processing
Pillow==11.1.0

# Regex
regex==2024.11.6

# Date utilities
python-dateutil==2.9.0.post0

# Math and statistics
sympy==1.13.1
mpmath==1.3.0

# Packaging and building
packaging==24.2
build==1.2.2.post1
pyproject-hooks==1.2.0

# Tokenization
tokenizers==0.21.1
jiter==0.9.0

# Flatbuffers
flatbuffers==25.2.10

# Hash functions
mmh3==5.1.0

# Certificates
certifi==2025.1.31

# Character encoding
charset-normalizer==3.4.1

# URL handling
urllib3==2.3.0
idna==3.10

# HTML/XML parsing
soupsieve==2.6

# Cryptography
rsa==4.9
pyasn1==0.6.1
pyasn1-modules==0.4.1

# Protobuf
protobuf==5.29.3

# Starlette
starlette==0.46.1
asgiref==3.8.1

# Machine learning extras
joblib==1.4.2
threadpoolctl==3.6.0
safetensors==0.5.3

# Kubernetes (optional)
kubernetes==32.0.1

# Deprecated utilities
Deprecated==1.2.18

# System monitoring
psutil

# Duration parsing
durationpy==0.9

# Override utilities
overrides==7.7.0

# Analytics
posthog==3.20.0

# Shell utilities
shellingham==1.5.4

# Time utilities
monotonic==1.6

# Distribution detection
distro==1.9.0

# JSON patching
jsonpatch==1.33
jsonpointer==3.0.0

# SQL query builder
PyPika==0.48.9

# Hugging Face hub
huggingface-hub==0.29.3

# Tenacity (retry)
tenacity==9.0.0

# Pygments (syntax highlighting)
Pygments==2.19.1
"""
        
        try:
            with open(self.fixed_requirements_file, 'w', encoding='utf-8') as f:
                f.write(fixed_requirements)
            self.print_step(f"Created fixed requirements file: {self.fixed_requirements_file}", "SUCCESS")
            return True
        except Exception as e:
            self.print_step(f"Failed to create fixed requirements: {e}", "ERROR")
            return False
    
    def install_dependencies(self) -> bool:
        """Install all dependencies with proper handling"""
        self.print_header("PHASE 3: DEPENDENCY INSTALLATION")
        
        # Upgrade pip first
        self.print_step("Upgrading pip to latest version", "INFO")
        success, stdout, stderr = self.run_command([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], "Upgrading pip")
        
        if not success:
            self.print_step(f"Failed to upgrade pip: {stderr}", "WARNING")
        
        # Install wheel and setuptools
        success, stdout, stderr = self.run_command([
            sys.executable, "-m", "pip", "install", "--upgrade", "wheel", "setuptools"
        ], "Installing wheel and setuptools")
        
        if not success:
            self.print_step(f"Failed to install wheel/setuptools: {stderr}", "WARNING")
        
        # Install dependencies in stages to handle conflicts
        stages = [
            # Stage 1: Core dependencies
            [
                "fastapi==0.115.11",
                "uvicorn[standard]==0.34.0", 
                "python-dotenv==1.0.1",
                "pydantic==2.10.6",
                "requests==2.32.3"
            ],
            
            # Stage 2: Data and ML foundations
            [
                "numpy==1.26.4",
                "pandas==2.2.2", 
                "scipy==1.13.0",
                "scikit-learn==1.6.1"
            ],
            
            # Stage 3: PyTorch and transformers
            [
                "torch==2.6.0",
                "transformers==4.49.0",
                "sentence-transformers==3.4.1",
                "tiktoken==0.9.0"
            ],
            
            # Stage 4: Vector database
            [
                "chromadb==0.6.3",
                "chroma-hnswlib==0.7.6"
            ],
            
            # Stage 5: LangChain ecosystem
            [
                "langchain==0.3.20",
                "langchain-core==0.3.45",
                "langchain-openai==0.3.8",
                "langchain-chroma==0.2.2",
                "langgraph==0.3.10",
                "langgraph-checkpoint==2.0.19",
                "langgraph-prebuilt==0.1.3"
            ],
            
            # Stage 6: Streamlit and visualization
            [
                "streamlit==1.35.0",
                "plotly==5.22.0"
            ],
            
            # Stage 7: SEC specific tools
            [
                "sec-edgar-downloader==5.0.3",
                "beautifulsoup4==4.13.3"
            ],
            
            # Stage 8: All remaining packages
            [
                "openai==1.66.3",
                "SQLAlchemy==2.0.39",
                "pytest==8.2.1",
                "pytest-cov==5.0.0",
                "alembic==1.13.1",
                "jupyter==1.0.0",
                "networkx==3.3",
                "onnxruntime==1.18.0"
            ]
        ]
        
        for i, stage_packages in enumerate(stages, 1):
            self.print_step(f"Installing Stage {i} packages", "INFO")
            
            for package in stage_packages:
                success, stdout, stderr = self.run_command([
                    sys.executable, "-m", "pip", "install", "--upgrade", package
                ], f"Installing {package}", timeout=600)
                
                if success:
                    self.print_step(f"Successfully installed {package}", "SUCCESS")
                else:
                    self.print_step(f"Failed to install {package}: {stderr[:200]}", "ERROR")
                    
            # Small delay between stages
            time.sleep(2)
        
        return True
    
    def validate_imports(self) -> bool:
        """Validate that all critical imports work"""
        self.print_header("PHASE 4: IMPORT VALIDATION")
        
        critical_imports = [
            ("fastapi", "FastAPI"),
            ("streamlit", "Streamlit"),
            ("pandas", "Pandas"),
            ("numpy", "NumPy"),
            ("plotly", "Plotly"),
            ("openai", "OpenAI"),
            ("chromadb", "ChromaDB"),
            ("langchain", "LangChain"),
            ("torch", "PyTorch"),
            ("transformers", "Transformers"),
            ("sec_edgar_downloader", "SEC Edgar Downloader"),
            ("beautifulsoup4", "BeautifulSoup4"),
            ("sqlalchemy", "SQLAlchemy"),
            ("dotenv", "Python-dotenv"),
            ("uvicorn", "Uvicorn")
        ]
        
        failed_imports = []
        
        for module_name, display_name in critical_imports:
            try:
                # Handle special import cases
                if module_name == "beautifulsoup4":
                    import bs4
                elif module_name == "dotenv":
                    from dotenv import load_dotenv
                else:
                    importlib.import_module(module_name)
                    
                self.print_step(f"{display_name} import successful", "SUCCESS")
            except ImportError as e:
                self.print_step(f"{display_name} import failed: {e}", "ERROR")
                failed_imports.append(display_name)
        
        if failed_imports:
            self.print_step(f"Failed imports: {', '.join(failed_imports)}", "ERROR")
            return False
        else:
            self.print_step("All critical imports successful", "SUCCESS")
            return True
    
    def test_application_components(self) -> bool:
        """Test that application components can be imported"""
        self.print_header("PHASE 5: APPLICATION COMPONENT TESTING")
        
        # Add project root to Python path
        sys.path.insert(0, str(self.project_root))
        
        app_components = [
            ("app.core.config", "Core Configuration"),
            ("app.services.sql_storage", "SQL Storage Service"),
            ("app.services.embedding", "Embedding Service"),
            ("app.services.chatbot", "Chatbot Service"), 
            ("app.services.sec_scanner", "SEC Scanner"),
            ("app.services.downloader", "SEC Downloader"),
            ("app.utils.logger", "Logger Utilities")
        ]
        
        failed_components = []
        
        for module_name, display_name in app_components:
            try:
                importlib.import_module(module_name)
                self.print_step(f"{display_name} import successful", "SUCCESS")
            except ImportError as e:
                self.print_step(f"{display_name} import failed: {e}", "ERROR")
                failed_components.append(display_name)
            except Exception as e:
                self.print_step(f"{display_name} initialization error: {e}", "WARNING")
        
        if failed_components:
            self.print_step(f"Failed components: {', '.join(failed_components)}", "ERROR")
            return False
        else:
            self.print_step("All application components load successfully", "SUCCESS")
            return True
    
    def check_environment_setup(self) -> bool:
        """Check environment variables and configuration"""
        self.print_header("PHASE 6: ENVIRONMENT CONFIGURATION CHECK")
        
        required_env_vars = ["OPENAI_API_KEY", "SEC_EMAIL"]
        optional_env_vars = ["FILINGS_DIR", "DATABASE_URL"]
        
        all_present = True
        
        for var in required_env_vars:
            if os.getenv(var):
                self.print_step(f"{var} is set", "SUCCESS")
            else:
                self.print_step(f"{var} is missing (REQUIRED)", "ERROR")
                all_present = False
                
        for var in optional_env_vars:
            if os.getenv(var):
                self.print_step(f"{var} is set", "SUCCESS")
            else:
                self.print_step(f"{var} is not set (optional)", "INFO")
        
        # Check for .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            self.print_step("Found .env file", "SUCCESS")
        else:
            self.print_step("No .env file found - you may need to create one", "WARNING")
            
        return all_present
    
    def setup_directories(self) -> bool:
        """Set up required directories"""
        self.print_header("PHASE 7: DIRECTORY SETUP")
        
        required_dirs = [
            "data/db",
            "embeddings/chromadb",
            "sec-edgar-filings",
            "logs"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                self.print_step(f"Directory ready: {dir_path}", "SUCCESS")
            except Exception as e:
                self.print_step(f"Failed to create directory {dir_path}: {e}", "ERROR")
                return False
                
        return True
    
    def run_application_tests(self) -> bool:
        """Run basic application functionality tests"""
        self.print_header("PHASE 8: APPLICATION FUNCTIONALITY TESTS")
        
        sys.path.insert(0, str(self.project_root))
        
        try:
            # Test database connection
            from app.services.sql_storage import SQLStorage
            sql_storage = SQLStorage()
            self.print_step("Database connection test passed", "SUCCESS")
            
            # Test embedding service initialization  
            from app.services.embedding import EmbeddingService
            # Only test if OpenAI key is available
            if os.getenv("OPENAI_API_KEY"):
                embedding_service = EmbeddingService()
                self.print_step("Embedding service initialization test passed", "SUCCESS")
            else:
                self.print_step("Skipping embedding service test (no OpenAI key)", "WARNING")
            
            # Test configuration loading
            from app.core.config import TICKERS, FILING_TYPES
            self.print_step("Configuration loading test passed", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.print_step(f"Application functionality test failed: {e}", "ERROR")
            return False
    
    def generate_summary_report(self, all_phases_passed: bool) -> None:
        """Generate a comprehensive summary report"""
        self.print_header("SETUP COMPLETION SUMMARY", Colors.MAGENTA if all_phases_passed else Colors.RED)
        
        if all_phases_passed:
            self.print_step("🎉 ALL SETUP PHASES COMPLETED SUCCESSFULLY!", "SUCCESS")
            self.print_step("", "INFO")
            self.print_step("Your SEC Filing Scanner is ready to run!", "SUCCESS")
            self.print_step("", "INFO")
            self.print_step("Next steps:", "INFO")
            self.print_step("1. Ensure your .env file has OPENAI_API_KEY and SEC_EMAIL", "INFO")
            self.print_step("2. Start the FastAPI backend: uvicorn app.main:app --reload", "INFO")
            self.print_step("3. Start the Streamlit frontend: streamlit run streamlit_app.py", "INFO")
            self.print_step("4. Or use Docker: docker-compose -f docker/docker-compose.yml up", "INFO")
        else:
            self.print_step("❌ SETUP INCOMPLETE - Some phases failed", "ERROR")
            self.print_step("", "INFO")
            self.print_step("Please address the errors above and run the setup again", "ERROR")
            self.print_step("", "INFO")
            self.print_step("Common solutions:", "INFO")
            self.print_step("• Update Python to 3.8-3.11 if using 3.12+", "INFO")
            self.print_step("• Use a virtual environment", "INFO")
            self.print_step("• Check internet connection for downloads", "INFO")
            self.print_step("• Install Visual Studio Build Tools on Windows", "INFO")
    
    def run_complete_setup(self) -> bool:
        """Run the complete setup process"""
        self.print_header("SEC FILING SCANNER - COMPREHENSIVE SETUP", Colors.MAGENTA)
        self.print_step("Starting comprehensive setup and validation process", "INFO")
        
        phases = [
            ("System Requirements Check", self.check_system_requirements),
            ("Fixed Requirements Creation", self.create_fixed_requirements),
            ("Dependency Installation", self.install_dependencies),
            ("Import Validation", self.validate_imports),
            ("Application Component Testing", self.test_application_components),
            ("Environment Configuration Check", self.check_environment_setup),
            ("Directory Setup", self.setup_directories),
            ("Application Functionality Tests", self.run_application_tests)
        ]
        
        all_phases_passed = True
        
        for phase_name, phase_function in phases:
            self.print_step(f"Starting: {phase_name}", "INFO")
            try:
                if not phase_function():
                    self.print_step(f"FAILED: {phase_name}", "ERROR")
                    all_phases_passed = False
                    # Continue with other phases to get full picture
                else:
                    self.print_step(f"COMPLETED: {phase_name}", "SUCCESS")
            except Exception as e:
                self.print_step(f"ERROR in {phase_name}: {e}", "ERROR")
                all_phases_passed = False
        
        self.generate_summary_report(all_phases_passed)
        return all_phases_passed


def main():
    """Main entry point"""
    setup = ComprehensiveSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
SEC Filing Scanner - Comprehensive Setup Script

Usage:
    python comprehensive_setup.py          # Run complete setup
    python comprehensive_setup.py --help   # Show this help

This script will:
1. Check system requirements
2. Create fixed requirements.txt with compatible versions
3. Install all dependencies in staged approach
4. Validate all imports work correctly
5. Test application components
6. Check environment configuration
7. Set up required directories
8. Run basic functionality tests

Only proceeds to final validation when ALL requirements are satisfied.
        """)
        return
    
    success = setup.run_complete_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
