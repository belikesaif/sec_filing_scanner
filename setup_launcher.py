#!/usr/bin/env python3
"""
SEC Filing Scanner - Interactive Setup Launcher
This script helps users choose the right setup method for their needs.
"""

import os
import sys
import subprocess
from pathlib import Path

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
    END = '\033[0m'

def print_header(text: str, color=Colors.CYAN):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{color}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{color}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{color}{'='*80}{Colors.END}\n")

def print_option(number: int, title: str, description: str, recommended: bool = False):
    """Print a formatted option"""
    rec_text = f" {Colors.GREEN}(RECOMMENDED){Colors.END}" if recommended else ""
    print(f"{Colors.BOLD}{Colors.BLUE}[{number}]{Colors.END} {Colors.BOLD}{title}{Colors.END}{rec_text}")
    print(f"    {description}")
    print()

def run_script(script_name: str) -> bool:
    """Run a setup script and return success status"""
    try:
        result = subprocess.run([sys.executable, script_name], 
                               cwd=Path(__file__).parent,
                               capture_output=False,
                               text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.RED}Error running {script_name}: {e}{Colors.END}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version < (3, 8):
        print(f"{Colors.RED}Error: Python 3.8+ is required. You have {version.major}.{version.minor}.{version.micro}{Colors.END}")
        return False
    elif version >= (3, 12):
        print(f"{Colors.YELLOW}Warning: Python {version.major}.{version.minor} may have compatibility issues. Python 3.8-3.11 is recommended.{Colors.END}")
    else:
        print(f"{Colors.GREEN}Python version {version.major}.{version.minor}.{version.micro} is compatible.{Colors.END}")
    return True

def main():
    """Main interactive setup launcher"""
    print_header("SEC FILING SCANNER - SETUP LAUNCHER", Colors.MAGENTA)
    
    print(f"{Colors.BOLD}Welcome to the SEC Filing Scanner setup!{Colors.END}")
    print("This launcher will help you choose the right setup method for your needs.\n")
    
    # Check Python version first
    if not check_python_version():
        print(f"\n{Colors.RED}Please install Python 3.8-3.11 and try again.{Colors.END}")
        return
    
    print(f"\n{Colors.BOLD}Available Setup Options:{Colors.END}\n")
    
    print_option(
        1, 
        "Comprehensive Setup", 
        "Complete automated setup with validation (recommended for first-time users)",
        recommended=True
    )
    
    print_option(
        2,
        "Diagnostic Check",
        "Analyze your environment and identify issues (good for troubleshooting)"
    )
    
    print_option(
        3,
        "Debug & Repair",
        "Fix specific application issues and database problems"
    )
    
    print_option(
        4,
        "Manual Setup",
        "Show manual setup instructions (for advanced users)"
    )
    
    print_option(
        5,
        "Docker Setup",
        "Show Docker-based setup instructions"
    )
    
    print_option(
        6,
        "Exit",
        "Exit the setup launcher"
    )
    
    while True:
        try:
            choice = input(f"{Colors.BOLD}Enter your choice (1-6): {Colors.END}").strip()
            
            if choice == "1":
                print_header("RUNNING COMPREHENSIVE SETUP")
                print("This will perform a complete setup and validation...")
                if run_script("comprehensive_setup.py"):
                    print(f"\n{Colors.GREEN}✅ Comprehensive setup completed successfully!{Colors.END}")
                else:
                    print(f"\n{Colors.RED}❌ Setup encountered issues. Check the output above.{Colors.END}")
                break
                
            elif choice == "2":
                print_header("RUNNING DIAGNOSTIC CHECK")
                print("This will analyze your environment and identify issues...")
                if run_script("setup_and_check.py"):
                    print(f"\n{Colors.GREEN}✅ Diagnostic check completed.{Colors.END}")
                else:
                    print(f"\n{Colors.RED}❌ Diagnostic check encountered issues.{Colors.END}")
                break
                
            elif choice == "3":
                print_header("RUNNING DEBUG & REPAIR")
                print("This will attempt to fix common application issues...")
                if run_script("debug_and_fix.py"):
                    print(f"\n{Colors.GREEN}✅ Debug and repair completed.{Colors.END}")
                else:
                    print(f"\n{Colors.RED}❌ Debug and repair encountered issues.{Colors.END}")
                break
                
            elif choice == "4":
                print_header("MANUAL SETUP INSTRUCTIONS")
                print(f"""
{Colors.BOLD}Manual Setup Steps:{Colors.END}

1. {Colors.BOLD}Install Dependencies:{Colors.END}
   pip install --upgrade pip
   pip install -r requirements.txt

2. {Colors.BOLD}Create Environment File:{Colors.END}
   Create a '.env' file with:
   OPENAI_API_KEY=your_api_key_here
   SEC_EMAIL=your.email@example.com

3. {Colors.BOLD}Set Up Directories:{Colors.END}
   Create these directories:
   - data/db
   - embeddings/chromadb
   - sec-edgar-filings
   - logs

4. {Colors.BOLD}Test Installation:{Colors.END}
   python -c "from app.main import app; print('✅ App imports successfully')"

5. {Colors.BOLD}Run Application:{Colors.END}
   # FastAPI backend:
   uvicorn app.main:app --reload
   
   # Streamlit frontend:
   streamlit run streamlit_app.py

{Colors.BOLD}For detailed instructions, see SETUP_README.md{Colors.END}
                """)
                break
                
            elif choice == "5":
                print_header("DOCKER SETUP INSTRUCTIONS")
                print(f"""
{Colors.BOLD}Docker Setup Steps:{Colors.END}

1. {Colors.BOLD}Install Docker:{Colors.END}
   Download from https://docker.com/get-started

2. {Colors.BOLD}Create Environment File:{Colors.END}
   Create a '.env' file with:
   OPENAI_API_KEY=your_api_key_here
   SEC_EMAIL=your.email@example.com

3. {Colors.BOLD}Build and Run:{Colors.END}
   docker-compose -f docker/docker-compose.yml up --build

4. {Colors.BOLD}Access Application:{Colors.END}
   - Streamlit: http://localhost:8501
   - FastAPI: http://localhost:8000

{Colors.BOLD}For detailed instructions, see SETUP_README.md{Colors.END}
                """)
                break
                
            elif choice == "6":
                print(f"\n{Colors.BOLD}Thank you for using SEC Filing Scanner!{Colors.END}")
                print(f"For detailed setup instructions, see: {Colors.CYAN}SETUP_README.md{Colors.END}")
                break
                
            else:
                print(f"{Colors.RED}Invalid choice. Please enter a number between 1 and 6.{Colors.END}")
                continue
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Setup cancelled by user.{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")
            continue
    
    print(f"\n{Colors.BOLD}Setup launcher finished.{Colors.END}")
    print(f"If you need help, check {Colors.CYAN}SETUP_README.md{Colors.END} or run this script again.")

if __name__ == "__main__":
    main()
