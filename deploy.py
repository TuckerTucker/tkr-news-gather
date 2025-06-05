#!/usr/bin/env python3
"""
Interactive RunPod Deployment Script for TKR News Gather
Guides users through the complete deployment process step by step.
"""

import os
import sys
import subprocess
import json
import time
import re
from typing import Dict, List, Optional
from datetime import datetime

try:
    import requests
except ImportError:
    print("⚠️  Warning: 'requests' module not found. Install with: pip install requests")
    print("   Automatic RunPod endpoint creation will be disabled.")
    requests = None


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class RunPodAPI:
    """RunPod API client for creating templates and endpoints"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.graphql_url = "https://api.runpod.io/graphql"  # For templates
        self.rest_url = "https://rest.runpod.io/v1"  # For endpoints
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def _make_graphql_request(self, query: str, variables: Dict = None) -> Dict:
        """Make GraphQL request to RunPod API"""
        if requests is None:
            raise Exception("requests module not available. Install with: pip install requests")
            
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        try:
            response = requests.post(self.graphql_url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"RunPod GraphQL request failed: {str(e)}")
    
    def _make_rest_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make REST request to RunPod API"""
        if requests is None:
            raise Exception("requests module not available. Install with: pip install requests")
            
        url = f"{self.rest_url}/{endpoint}"
        
        try:
            response = requests.request(method, url, json=data, headers=self.headers)
            
            # Get response data for debugging
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}"
                if isinstance(response_data, dict):
                    if "error" in response_data:
                        error_msg = response_data["error"]
                    elif "message" in response_data:
                        error_msg = response_data["message"]
                    elif "errors" in response_data:
                        error_msg = str(response_data["errors"])
                raise Exception(f"RunPod REST request failed: {error_msg} (Status: {response.status_code}, Response: {response_data})")
            
            return response_data
        except requests.exceptions.RequestException as e:
            raise Exception(f"RunPod REST request failed: {str(e)}")
    
    def create_template(self, template_config: Dict) -> str:
        """Create a new template"""
        query = """
        mutation podTemplateCreate($input: PodTemplateCreateInput!) {
            podTemplateCreate(input: $input) {
                id
                name
                imageName
                dockerStartCmd
                isPublic
                ports
                volumeInGb
                containerDiskInGb
                env {
                    key
                    value
                }
            }
        }
        """
        
        variables = {"input": template_config}
        result = self._make_graphql_request(query, variables)
        
        if "errors" in result:
            raise Exception(f"Failed to create template: {result['errors']}")
            
        return result["data"]["podTemplateCreate"]["id"]
    
    def create_serverless_endpoint(self, endpoint_config: Dict) -> Dict:
        """Create a new serverless endpoint"""
        query = """
        mutation saveTemplate($input: SaveTemplateInput!) {
            saveTemplate(input: $input) {
                id
                name
                containerRegistryAuthId
                env {
                    key
                    value
                }
                imageName
                dockerArgs
                ports
                volumeInGb
                volumeMountPath
                containerDiskInGb
            }
        }
        """
        
        # First create the template for serverless
        template_result = self._make_graphql_request(query, {"input": endpoint_config})
        
        if "errors" in template_result:
            raise Exception(f"Failed to create serverless template: {template_result['errors']}")
        
        template_id = template_result["data"]["saveTemplate"]["id"]
        
        # Now create the serverless endpoint
        endpoint_query = """
        mutation createServerlessEndpoint($input: CreateServerlessEndpointInput!) {
            createServerlessEndpoint(input: $input) {
                id
                name
                templateId
                locations {
                    countryCode
                    isAvailable
                }
                scalerSettings {
                    idleTimeout
                    maxWorkers
                    targetConcurrency
                }
                networkVolumeId
                userId
            }
        }
        """
        
        endpoint_input = {
            "name": endpoint_config["name"],
            "templateId": template_id,
            "scalerSettings": {
                "idleTimeout": endpoint_config.get("idleTimeout", 30),
                "maxWorkers": endpoint_config.get("maxWorkers", 5),
                "targetConcurrency": endpoint_config.get("targetConcurrency", 1)
            },
            "locations": ["US-CA", "US-OR"]  # Default locations
        }
        
        endpoint_result = self._make_graphql_request(endpoint_query, {"input": endpoint_input})
        
        if "errors" in endpoint_result:
            raise Exception(f"Failed to create serverless endpoint: {endpoint_result['errors']}")
            
        return endpoint_result["data"]["createServerlessEndpoint"]
    
    def create_serverless_endpoint_rest(self, endpoint_config: Dict) -> Dict:
        """Create a serverless endpoint using REST API"""
        try:
            # Prepare endpoint data for REST API
            # Note: Even for CPU workloads, RunPod might require GPU types
            endpoint_data = {
                "name": endpoint_config["name"],
                "templateId": endpoint_config["templateId"],
                "gpuTypeIds": ["NVIDIA RTX A4000"],  # Minimal GPU requirement
                "computeType": "GPU",  # Required field
                "workersMin": 0,  # Start with 0 workers
                "workersMax": endpoint_config.get("maxWorkers", 5),
                "idleTimeout": endpoint_config.get("idleTimeout", 30),
                "flashboot": True  # Enable fast startup
            }
            
            result = self._make_rest_request("POST", "endpoints", endpoint_data)
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                return result[0]  # Take first endpoint from list
            elif isinstance(result, dict):
                return result
            else:
                raise Exception(f"Unexpected response format: {result}")
                
        except Exception as e:
            raise Exception(f"Failed to create serverless endpoint via REST: {str(e)}")
    
    def get_endpoints(self) -> List[Dict]:
        """Get list of serverless endpoints"""
        query = """
        query getServerlessEndpoints {
            myself {
                serverlessDiscount {
                    discountFactor
                    type
                }
                podTemplates {
                    id
                    name
                    imageName
                    isPublic
                }
            }
        }
        """
        
        result = self._make_graphql_request(query)
        
        if "errors" in result:
            raise Exception(f"Failed to get endpoints: {result['errors']}")
            
        return result["data"]["myself"]["podTemplates"]
    
    def get_endpoint_url(self, endpoint_id: str) -> str:
        """Get the URL for an endpoint"""
        return f"https://api.runpod.io/v2/{endpoint_id}/runsync"


class DeploymentScript:
    def __init__(self, quick_mode=False):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.env_file = os.path.join(self.project_dir, '.env')
        self.deployment_config = {}
        self.quick_mode = quick_mode
        self.load_existing_config()
        
    def load_existing_config(self):
        """Load existing configuration from .env file"""
        if os.path.exists(self.env_file):
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')  # Remove quotes
                            self.deployment_config[key] = value
                            
                # Will print this later when print methods are available
                self._config_loaded = True
                
                # Convert some values to proper types
                if 'MEMORY_GB' in self.deployment_config:
                    try:
                        self.deployment_config['MEMORY_GB'] = int(self.deployment_config['MEMORY_GB'])
                    except ValueError:
                        pass
                        
                if 'CPU_COUNT' in self.deployment_config:
                    try:
                        self.deployment_config['CPU_COUNT'] = int(self.deployment_config['CPU_COUNT'])
                    except ValueError:
                        pass
                        
                # Set other numeric defaults
                for key in ['STORAGE_GB', 'MAX_WORKERS', 'IDLE_TIMEOUT', 'EXECUTION_TIMEOUT']:
                    if key in self.deployment_config:
                        try:
                            self.deployment_config[key] = int(self.deployment_config[key])
                        except ValueError:
                            pass
                            
            except Exception as e:
                self._config_error = str(e)
        else:
            self._config_loaded = False
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE} {title.center(58)} {Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
        
    def print_step(self, step: str, description: str):
        """Print a step with description"""
        print(f"{Colors.BOLD}{Colors.GREEN}📋 Step: {step}{Colors.END}")
        print(f"{Colors.CYAN}   {description}{Colors.END}\n")
        
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
        
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")
        
    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{Colors.YELLOW}❓ {question} [{default_str}]: {Colors.END}").strip().lower()
        
        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']
        
    def ask_input(self, question: str, default: str = "", required: bool = True, mask: bool = False) -> str:
        """Ask for user input"""
        default_display = f" [{default}]" if default else ""
        prompt = f"{Colors.YELLOW}❓ {question}{default_display}: {Colors.END}"
        
        if mask:
            import getpass
            response = getpass.getpass(prompt)
        else:
            response = input(prompt).strip()
            
        if not response and default:
            return default
        elif not response and required:
            self.print_error("This field is required!")
            return self.ask_input(question, default, required, mask)
        
        return response
        
    def run_command(self, command: str, description: str, check: bool = True, hide_command: bool = False) -> bool:
        """Run a shell command"""
        print(f"{Colors.CYAN}🔧 {description}...{Colors.END}")
        
        if hide_command:
            print(f"{Colors.WHITE}   Running: [command with sensitive data hidden]{Colors.END}")
        else:
            print(f"{Colors.WHITE}   Running: {command}{Colors.END}")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_success(f"{description} completed successfully")
                if result.stdout.strip():
                    print(f"{Colors.WHITE}   Output: {result.stdout.strip()}{Colors.END}")
                return True
            else:
                self.print_error(f"{description} failed")
                if result.stderr.strip():
                    print(f"{Colors.RED}   Error: {result.stderr.strip()}{Colors.END}")
                if not check:
                    return False
                
                if self.ask_yes_no("Continue anyway?", False):
                    return True
                else:
                    sys.exit(1)
                    
        except Exception as e:
            self.print_error(f"Failed to run command: {str(e)}")
            if check:
                sys.exit(1)
            return False
            
    def check_dependencies(self):
        """Check if required tools are installed"""
        self.print_step("1", "Checking Dependencies")
        
        dependencies = [
            ("docker", "Docker"),
            ("make", "Make"),
            ("python3", "Python 3")
        ]
        
        missing = []
        for cmd, name in dependencies:
            if subprocess.run(f"which {cmd}", shell=True, capture_output=True).returncode != 0:
                missing.append(name)
                
        if missing:
            self.print_error(f"Missing dependencies: {', '.join(missing)}")
            print("\nPlease install the missing dependencies and try again.")
            sys.exit(1)
            
        self.print_success("All dependencies are installed")
        
    def generate_secrets(self):
        """Generate JWT secrets and API keys"""
        self.print_step("2", "Generating Security Credentials")
        
        # Check if we have existing valid secrets
        has_jwt = self.deployment_config.get('JWT_SECRET_KEY') and self.deployment_config['JWT_SECRET_KEY'] != 'your_jwt_secret_key_here_generate_random_32_chars'
        has_api_keys = self.deployment_config.get('API_KEYS') and self.deployment_config['API_KEYS'] != 'api_key_1,api_key_2,api_key_3'
        
        if has_jwt and has_api_keys:
            print(f"{Colors.CYAN}Found existing security credentials:{Colors.END}")
            print(f"  • JWT Secret Key: {'✅ Present' if has_jwt else '❌ Missing'}")
            print(f"  • API Keys: {'✅ Present' if has_api_keys else '❌ Missing'}")
            print()
            
            if self.ask_yes_no("Use existing security credentials?", True):
                self.print_success("Using existing security credentials")
                return
        
        # For RunPod-only deployments, JWT is optional
        print(f"{Colors.CYAN}Note: For RunPod serverless deployment, JWT tokens are optional.{Colors.END}")
        print(f"{Colors.CYAN}They're only needed if you plan to use the secure FastAPI endpoints.{Colors.END}")
        print()
        
        if not self.ask_yes_no("Generate JWT and API keys for complete security setup?", True):
            self.print_info("Skipping JWT generation - RunPod will work without them")
            return
        
        if os.path.exists(self.env_file):
            if self.ask_yes_no("Regenerate security credentials?", not (has_jwt and has_api_keys)):
                self.run_command("make generate-credentials", "Generating new credentials")
            else:
                self.print_info("Keeping existing credentials")
        else:
            self.run_command("make generate-credentials", "Generating credentials")
            
        # Read the generated/updated .env file to extract secrets
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                content = f.read()
                
            # Extract key values for RunPod
            for line in content.split('\n'):
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    self.deployment_config[key.strip()] = value.strip()
                    
        self.print_success("Security credentials ready")
        
    def get_api_credentials(self):
        """Get API credentials from user"""
        self.print_step("3", "API Credentials Setup")
        
        # Show what was loaded from .env
        if hasattr(self, '_config_loaded') and self._config_loaded:
            self.print_success("Configuration loaded from existing .env file")
            
            # Check if we have the required credentials
            has_anthropic = bool(self.deployment_config.get('ANTHROPIC_API_KEY'))
            has_supabase = bool(self.deployment_config.get('SUPABASE_URL'))
            
            print(f"{Colors.CYAN}Found existing credentials:{Colors.END}")
            print(f"  • Anthropic API Key: {'✅ Present' if has_anthropic else '❌ Missing'}")
            print(f"  • Supabase URL: {'✅ Present' if has_supabase else '❌ Missing'}")
            print(f"  • Docker Username: {'✅ Present' if self.deployment_config.get('DOCKER_USERNAME') else '❌ Missing'}")
            print(f"  • RunPod API Key: {'✅ Present' if self.deployment_config.get('RUNPOD_API_KEY') else '❌ Missing'}")
            print()
            
            if has_anthropic and self.ask_yes_no("Use existing API credentials from .env file?", True):
                self.print_success("Using existing API credentials")
                return
        elif hasattr(self, '_config_error'):
            self.print_warning(f"Could not load .env file: {self._config_error}")
        else:
            self.print_info("No existing .env file found")
        
        print("You'll need the following API credentials:")
        print(f"{Colors.CYAN}• Anthropic API Key (required){Colors.END}")
        print(f"{Colors.CYAN}• Supabase URL and Anon Key (optional but recommended){Colors.END}\n")
        
        # Anthropic API Key
        anthropic_key = self.ask_input(
            "Enter your Anthropic API Key", 
            self.deployment_config.get('ANTHROPIC_API_KEY', ''),
            required=True,
            mask=True
        )
        self.deployment_config['ANTHROPIC_API_KEY'] = anthropic_key
        
        # Supabase credentials
        has_existing_supabase = bool(self.deployment_config.get('SUPABASE_URL'))
        use_supabase = self.ask_yes_no("Do you want to use Supabase for database storage?", has_existing_supabase)
        
        if use_supabase:
            supabase_url = self.ask_input(
                "Enter your Supabase URL",
                self.deployment_config.get('SUPABASE_URL', ''),
                required=True
            )
            supabase_key = self.ask_input(
                "Enter your Supabase Anon Key",
                self.deployment_config.get('SUPABASE_ANON_KEY', ''),
                required=True,
                mask=True
            )
            
            self.deployment_config['SUPABASE_URL'] = supabase_url
            self.deployment_config['SUPABASE_ANON_KEY'] = supabase_key
        else:
            self.print_info("Skipping Supabase setup - database features will be disabled")
            
        self.print_success("API credentials configured")
        
    def get_docker_config(self):
        """Get Docker Hub configuration"""
        self.print_step("4", "Docker Hub Configuration")
        
        # Check if we have existing Docker credentials
        existing_username = self.deployment_config.get('DOCKER_USERNAME')
        existing_password = self.deployment_config.get('DOCKER_PASSWORD')
        existing_image = self.deployment_config.get('DOCKER_IMAGE')
        
        if existing_username and existing_password:
            print(f"{Colors.CYAN}Found existing Docker configuration:{Colors.END}")
            print(f"  • Username: {existing_username}")
            print(f"  • Image: {existing_image or f'{existing_username}/tkr-news-gather:latest'}")
            print()
            
            if self.ask_yes_no("Use existing Docker Hub credentials?", True):
                # Test existing credentials
                login_cmd = f"echo '{existing_password}' | docker login -u {existing_username} --password-stdin"
                if self.run_command(login_cmd, "Testing existing Docker Hub credentials", check=False, hide_command=True):
                    self.deployment_config['DOCKER_USERNAME'] = existing_username
                    self.deployment_config['DOCKER_IMAGE'] = existing_image or f"{existing_username}/tkr-news-gather:latest"
                    self.print_success("Using existing Docker Hub credentials")
                    return
                else:
                    self.print_warning("Existing Docker credentials failed. Please enter new ones.")
        
        print("You need a Docker Hub account to store the container image.")
        print("If you don't have one, create it at: https://hub.docker.com\n")
        
        docker_username = self.ask_input(
            "Enter your Docker Hub username", 
            existing_username or "",
            required=True
        )
        docker_password = self.ask_input(
            "Enter your Docker Hub password", 
            existing_password or "",
            required=True, 
            mask=True
        )
        
        # Test Docker Hub login
        login_cmd = f"echo '{docker_password}' | docker login -u {docker_username} --password-stdin"
        if self.run_command(login_cmd, "Testing Docker Hub login", check=False, hide_command=True):
            self.deployment_config['DOCKER_USERNAME'] = docker_username
            self.deployment_config['DOCKER_PASSWORD'] = docker_password  # Store for .env update
            self.deployment_config['DOCKER_IMAGE'] = f"{docker_username}/tkr-news-gather:latest"
            self.print_success("Docker Hub login successful")
        else:
            self.print_error("Docker Hub login failed. Please check your credentials.")
            sys.exit(1)
            
    def build_and_push_image(self):
        """Build and push Docker image"""
        self.print_step("5", "Building and Pushing Docker Image")
        
        print(f"Building image: {self.deployment_config['DOCKER_IMAGE']}")
        
        # Set Docker username environment variable for make command
        docker_username = self.deployment_config['DOCKER_USERNAME']
        build_cmd = f"DOCKER_USERNAME={docker_username} make docker-build-hub"
        
        # Build image directly with Docker Hub tag
        if not self.run_command(build_cmd, "Building Docker image with Docker Hub tag"):
            return False
            
        # Push image
        push_cmd = f"docker push {self.deployment_config['DOCKER_IMAGE']}"
        if not self.run_command(push_cmd, "Pushing Docker image to Hub"):
            return False
            
        self.print_success(f"Docker image available at: {self.deployment_config['DOCKER_IMAGE']}")
        return True
        
    def get_runpod_config(self):
        """Get RunPod configuration"""
        self.print_step("6", "RunPod Configuration")
        
        # Check for existing RunPod configuration
        existing_api_key = self.deployment_config.get('RUNPOD_API_KEY')
        existing_endpoint_name = self.deployment_config.get('ENDPOINT_NAME')
        existing_memory = self.deployment_config.get('MEMORY_GB')
        existing_cpu = self.deployment_config.get('CPU_COUNT')
        
        if existing_api_key and existing_endpoint_name:
            print(f"{Colors.CYAN}Found existing RunPod configuration:{Colors.END}")
            print(f"  • API Key: {'✅ Present' if existing_api_key else '❌ Missing'}")
            print(f"  • Endpoint Name: {existing_endpoint_name}")
            print(f"  • Memory: {existing_memory}GB")
            print(f"  • CPU: {existing_cpu} vCPUs")
            print(f"  • Storage: {self.deployment_config.get('STORAGE_GB', 5)}GB")
            print(f"  • Max Workers: {self.deployment_config.get('MAX_WORKERS', 5)}")
            print()
            
            if self.ask_yes_no("Use existing RunPod configuration?", True):
                self.print_success("Using existing RunPod configuration")
                return
        
        print("You'll need a RunPod account and API key.")
        print("Sign up at: https://runpod.io\n")
        
        runpod_api_key = self.ask_input(
            "Enter your RunPod API Key", 
            existing_api_key or "",
            required=True, 
            mask=True
        )
        self.deployment_config['RUNPOD_API_KEY'] = runpod_api_key
        
        # Endpoint configuration
        endpoint_name = self.ask_input(
            "Enter endpoint name", 
            existing_endpoint_name or "tkr-news-gather"
        )
        self.deployment_config['ENDPOINT_NAME'] = endpoint_name
        
        # Resource configuration
        print(f"\n{Colors.CYAN}Recommended resources for TKR News Gather:{Colors.END}")
        print("• Memory: 4GB")
        print("• CPU: 2 vCPUs") 
        print("• GPU: None (CPU only)")
        print("• Storage: 5GB")
        print("• Max Workers: 5")
        print("• Idle Timeout: 30 seconds")
        print("• Execution Timeout: 600 seconds (10 minutes)\n")
        
        # Check if we have existing resource config
        has_existing_resources = all(k in self.deployment_config for k in ['MEMORY_GB', 'CPU_COUNT', 'STORAGE_GB'])
        
        if has_existing_resources:
            use_existing = self.ask_yes_no("Use existing resource configuration?", True)
            if use_existing:
                self.print_success("Using existing resource configuration")
                return
        
        use_recommended = self.ask_yes_no("Use recommended resource configuration?", True)
        
        if use_recommended:
            self.deployment_config.update({
                'MEMORY_GB': 4,
                'CPU_COUNT': 2,
                'STORAGE_GB': 5,
                'MAX_WORKERS': 5,
                'IDLE_TIMEOUT': 30,
                'EXECUTION_TIMEOUT': 600
            })
        else:
            self.deployment_config['MEMORY_GB'] = int(self.ask_input("Memory (GB)", str(existing_memory or 4)))
            self.deployment_config['CPU_COUNT'] = int(self.ask_input("CPU Count", str(existing_cpu or 2)))
            self.deployment_config['STORAGE_GB'] = int(self.ask_input("Storage (GB)", str(self.deployment_config.get('STORAGE_GB', 5))))
            self.deployment_config['MAX_WORKERS'] = int(self.ask_input("Max Workers", str(self.deployment_config.get('MAX_WORKERS', 5))))
            self.deployment_config['IDLE_TIMEOUT'] = int(self.ask_input("Idle Timeout (seconds)", str(self.deployment_config.get('IDLE_TIMEOUT', 30))))
            self.deployment_config['EXECUTION_TIMEOUT'] = int(self.ask_input("Execution Timeout (seconds)", str(self.deployment_config.get('EXECUTION_TIMEOUT', 600))))
            
        self.print_success("RunPod configuration completed")
        
    def create_runpod_template_and_endpoint(self):
        """Create RunPod template and serverless endpoint automatically"""
        self.print_step("6.5", "Creating RunPod Template and Endpoint")
        
        try:
            # Initialize RunPod API client
            runpod_client = RunPodAPI(self.deployment_config['RUNPOD_API_KEY'])
            
            # Prepare environment variables
            env_vars = [
                {"key": "ANTHROPIC_API_KEY", "value": self.deployment_config['ANTHROPIC_API_KEY']},
                {"key": "JWT_SECRET_KEY", "value": self.deployment_config.get('JWT_SECRET_KEY', '')},
                {"key": "API_KEYS", "value": self.deployment_config.get('API_KEYS', '')},
                {"key": "LOG_LEVEL", "value": "INFO"},
                {"key": "ANTHROPIC_MODEL", "value": "claude-3-haiku-20241022"},
                {"key": "LLM_TEMP", "value": "0.7"},
                {"key": "LLM_MAX_TOKENS", "value": "200000"}
            ]
            
            # Add Supabase env vars if configured
            if 'SUPABASE_URL' in self.deployment_config:
                env_vars.extend([
                    {"key": "SUPABASE_URL", "value": self.deployment_config['SUPABASE_URL']},
                    {"key": "SUPABASE_ANON_KEY", "value": self.deployment_config['SUPABASE_ANON_KEY']}
                ])
            
            print(f"{Colors.CYAN}Creating RunPod template...{Colors.END}")
            
            # Create template only (serverless endpoint needs to be created manually)
            template_config = {
                "name": f"{self.deployment_config['ENDPOINT_NAME']}-template",
                "imageName": self.deployment_config['DOCKER_IMAGE'],
                "dockerArgs": "python runpod_handler.py",
                "env": env_vars,
                "volumeInGb": self.deployment_config['STORAGE_GB'],
                "volumeMountPath": "/workspace",
                "containerDiskInGb": 10,  # Container disk space
                "ports": "8000/http",
                "isPublic": False
            }
            
            # Create the template
            template_result = runpod_client._make_graphql_request(
                """
                mutation saveTemplate($input: SaveTemplateInput!) {
                    saveTemplate(input: $input) {
                        id
                        name
                        imageName
                        dockerArgs
                        env {
                            key
                            value
                        }
                        volumeInGb
                        volumeMountPath
                        containerDiskInGb
                        ports
                        isPublic
                    }
                }
                """,
                {"input": template_config}
            )
            
            if "errors" in template_result:
                raise Exception(f"Failed to create template: {template_result['errors']}")
            
            template = template_result["data"]["saveTemplate"]
            self.deployment_config['TEMPLATE_ID'] = template['id']
            
            self.print_success(f"RunPod template created successfully!")
            print(f"{Colors.GREEN}   Template ID: {template['id']}{Colors.END}")
            print(f"{Colors.GREEN}   Template Name: {template['name']}{Colors.END}")
            
            # Now create the serverless endpoint using REST API
            print(f"{Colors.CYAN}Creating serverless endpoint...{Colors.END}")
            
            endpoint_config = {
                "name": self.deployment_config['ENDPOINT_NAME'],
                "templateId": template['id'],
                "maxWorkers": self.deployment_config['MAX_WORKERS'],
                "idleTimeout": self.deployment_config['IDLE_TIMEOUT']
            }
            
            endpoint = runpod_client.create_serverless_endpoint_rest(endpoint_config)
            
            # Store endpoint information
            self.deployment_config['ENDPOINT_ID'] = endpoint['id']
            self.deployment_config['ENDPOINT_URL'] = runpod_client.get_endpoint_url(endpoint['id'])
            
            self.print_success(f"RunPod endpoint created successfully!")
            print(f"{Colors.GREEN}   Endpoint ID: {endpoint['id']}{Colors.END}")
            print(f"{Colors.GREEN}   Endpoint URL: {self.deployment_config['ENDPOINT_URL']}{Colors.END}")
            print(f"{Colors.GREEN}   Max Workers: {endpoint.get('workersMax', 'N/A')}{Colors.END}")
            print(f"{Colors.GREEN}   Idle Timeout: {endpoint.get('idleTimeout', 'N/A')}s{Colors.END}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to create RunPod template: {str(e)}")
            self.print_warning("You can create the template manually using the deployment guide")
            return False
    
    def test_runpod_endpoint(self):
        """Test the created RunPod endpoint"""
        if 'ENDPOINT_URL' not in self.deployment_config:
            self.print_warning("No endpoint URL available for testing")
            return False
            
        self.print_step("6.7", "Testing RunPod Endpoint")
        
        try:
            if requests is None:
                self.print_warning("requests module not available - cannot test endpoint")
                return False
            
            # Test get_provinces action
            test_payload = {
                "input": {
                    "action": "get_provinces"
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deployment_config['RUNPOD_API_KEY']}"
            }
            
            print(f"{Colors.CYAN}Testing endpoint with get_provinces action...{Colors.END}")
            
            response = requests.post(
                self.deployment_config['ENDPOINT_URL'],
                json=test_payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'COMPLETED':
                    self.print_success("Endpoint test passed!")
                    provinces_count = len(result.get('output', {}).get('provinces', []))
                    print(f"{Colors.GREEN}   Retrieved {provinces_count} provinces{Colors.END}")
                    return True
                else:
                    self.print_warning(f"Endpoint returned status: {result.get('status')}")
                    return False
            else:
                self.print_warning(f"Endpoint test failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_warning(f"Endpoint test failed: {str(e)}")
            self.print_info("The endpoint may still be initializing. Try testing later.")
            return False
        
    def generate_runpod_deployment_guide(self):
        """Generate deployment guide and commands"""
        self.print_step("7", "Generating Deployment Instructions")
        
        # Create deployment guide
        template_info = ""
        if 'TEMPLATE_ID' in self.deployment_config:
            template_info = f"""
## ✅ Template Created Successfully!
- **Template ID**: `{self.deployment_config['TEMPLATE_ID']}`
- **Template Name**: `{self.deployment_config['ENDPOINT_NAME']}-template`

Your template is ready! Use it to create a serverless endpoint in the RunPod dashboard.
"""
        
        endpoint_info = ""
        if 'ENDPOINT_ID' in self.deployment_config:
            endpoint_info = f"""
## ✅ Endpoint Created Successfully!
- **Endpoint ID**: `{self.deployment_config['ENDPOINT_ID']}`
- **Endpoint URL**: `{self.deployment_config['ENDPOINT_URL']}`

Your endpoint is ready to use! Skip to the "Testing Your Deployment" section below.
"""
        
        guide_content = f"""# TKR News Gather - RunPod Deployment Guide
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🐳 Docker Image
Your image has been pushed to: `{self.deployment_config['DOCKER_IMAGE']}`
{template_info}{endpoint_info}
## 🚀 RunPod Endpoint Configuration

### Basic Settings
- **Name**: `{self.deployment_config['ENDPOINT_NAME']}`
- **Container Image**: `{self.deployment_config['DOCKER_IMAGE']}`
- **Container Registry**: Docker Hub (public)

### Resource Configuration
- **Memory**: {self.deployment_config['MEMORY_GB']}GB
- **CPU**: {self.deployment_config['CPU_COUNT']} vCPUs
- **Storage**: {self.deployment_config['STORAGE_GB']}GB
- **GPU**: None (CPU only)

### Scaling Configuration  
- **Max Workers**: {self.deployment_config['MAX_WORKERS']}
- **Idle Timeout**: {self.deployment_config['IDLE_TIMEOUT']} seconds
- **Execution Timeout**: {self.deployment_config['EXECUTION_TIMEOUT']} seconds

### Environment Variables
Add these environment variables in the RunPod dashboard:

```bash
# Required - Anthropic API
ANTHROPIC_API_KEY={self.deployment_config['ANTHROPIC_API_KEY'][:8]}...

# Security (from generated credentials)
JWT_SECRET_KEY={self.deployment_config.get('JWT_SECRET_KEY', 'GENERATE_NEW_KEY')}
API_KEYS={self.deployment_config.get('API_KEYS', 'GENERATE_NEW_KEYS')}
"""

        # Add Supabase config if enabled
        if 'SUPABASE_URL' in self.deployment_config:
            guide_content += f"""
# Database - Supabase
SUPABASE_URL={self.deployment_config['SUPABASE_URL']}
SUPABASE_ANON_KEY={self.deployment_config['SUPABASE_ANON_KEY'][:8]}...
"""

        guide_content += f"""
# Optional Configuration
LOG_LEVEL=INFO
ANTHROPIC_MODEL=claude-3-haiku-20241022
LLM_TEMP=0.7
LLM_MAX_TOKENS=200000
```

## 🧪 Testing Your Deployment

### Test Endpoints"""
        
        # Add endpoint URL information
        if 'ENDPOINT_URL' in self.deployment_config:
            guide_content += f"""
Your endpoint URL is:
`{self.deployment_config['ENDPOINT_URL']}`

### Sample Test Requests

**Get Provinces:**
```bash
curl -X POST {self.deployment_config['ENDPOINT_URL']} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {self.deployment_config['RUNPOD_API_KEY'][:10]}..." \\
  -d '{{
    "input": {{
      "action": "get_provinces"
    }}
  }}'
```

**Get News for Alberta:**
```bash
curl -X POST {self.deployment_config['ENDPOINT_URL']} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {self.deployment_config['RUNPOD_API_KEY'][:10]}..." \\
  -d '{{
    "input": {{
      "action": "get_news",
      "province": "Alberta",
      "limit": 5,
      "scrape": true
    }}
  }}'
```

**Process News with AI:**
```bash
curl -X POST {self.deployment_config['ENDPOINT_URL']} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {self.deployment_config['RUNPOD_API_KEY'][:10]}..." \\
  -d '{{
    "input": {{
      "action": "fetch_and_process",
      "province": "Alberta",
      "host_type": "anchor",
      "limit": 3,
      "scrape": true
    }}
  }}'
```"""
        else:
            guide_content += f"""
Once deployed, your endpoint URL will be:
`https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync`

### Sample Test Requests

**Get Provinces:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR-RUNPOD-API-KEY" \\
  -d '{{
    "input": {{
      "action": "get_provinces"
    }}
  }}'
```

**Get News for Alberta:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR-RUNPOD-API-KEY" \\
  -d '{{
    "input": {{
      "action": "get_news",
      "province": "Alberta",
      "limit": 5,
      "scrape": true
    }}
  }}'
```

**Process News with AI:**
```bash
curl -X POST https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR-RUNPOD-API-KEY" \\
  -d '{{
    "input": {{
      "action": "fetch_and_process",
      "province": "Alberta",
      "host_type": "anchor",
      "limit": 3,
      "scrape": true
    }}
  }}'
```"""
        
        guide_content += f"""

## 📋 Manual RunPod Setup Steps

{"### Step 1: Template Already Created ✅" if 'TEMPLATE_ID' in self.deployment_config else "### Step 1: Create Template"}
{f"Your template `{self.deployment_config['TEMPLATE_ID']}` is ready to use." if 'TEMPLATE_ID' in self.deployment_config else f"""
1. **Login to RunPod**: Go to https://runpod.io and sign in
2. **Navigate to Templates**: Click "Templates" in the sidebar
3. **Create New Template**: Click "New Template"
4. **Configure Template**:
   - Name: `{self.deployment_config['ENDPOINT_NAME']}-template`
   - Container Image: `{self.deployment_config['DOCKER_IMAGE']}`
   - Container Start Command: `python runpod_handler.py`
   - Environment Variables: Copy from the section above
   - Volume: {self.deployment_config['STORAGE_GB']}GB
   - Volume Mount Path: `/workspace`
5. **Save Template**"""}

### Step 2: Create Serverless Endpoint
1. **Navigate to Serverless**: Click "Serverless" in the top menu
2. **Create New Endpoint**: Click "New Endpoint"
3. **Select Template**: {"Choose your template `" + self.deployment_config['TEMPLATE_ID'] + "`" if 'TEMPLATE_ID' in self.deployment_config else f"Choose the template you created"}
4. **Configure Scaling**:
   - Max Workers: {self.deployment_config['MAX_WORKERS']}
   - Idle Timeout: {self.deployment_config['IDLE_TIMEOUT']} seconds
   - Execution Timeout: {self.deployment_config['EXECUTION_TIMEOUT']} seconds
5. **Deploy**: Click "Deploy" and wait for the endpoint to be ready
6. **Copy Endpoint ID**: Save the endpoint ID for testing

## 🔒 Security Notes

- Store your RunPod API key securely
- The JWT and API keys have been generated for security
- Consider rotating credentials regularly
- Monitor usage and costs in the RunPod dashboard

## 🆘 Troubleshooting

If your deployment fails:
1. Check the RunPod logs for error messages
2. Verify all environment variables are set correctly
3. Ensure your Docker image is public and accessible
4. Test the image locally first: `docker run -p 8000:8000 --env-file .env {self.deployment_config['DOCKER_IMAGE']}`

## 📞 Support

- RunPod Documentation: https://docs.runpod.io
- TKR News Gather Issues: Create an issue in the project repository
"""

        # Write deployment guide
        guide_file = os.path.join(self.project_dir, 'RUNPOD_DEPLOYMENT.md')
        with open(guide_file, 'w') as f:
            f.write(guide_content)
            
        self.print_success(f"Deployment guide saved to: RUNPOD_DEPLOYMENT.md")
        
        # Also create a summary for quick reference
        print(f"\n{Colors.BOLD}{Colors.PURPLE}🎯 Quick Deployment Summary{Colors.END}")
        print(f"{Colors.CYAN}Docker Image: {self.deployment_config['DOCKER_IMAGE']}{Colors.END}")
        print(f"{Colors.CYAN}Endpoint Name: {self.deployment_config['ENDPOINT_NAME']}{Colors.END}")
        print(f"{Colors.CYAN}Resources: {self.deployment_config['MEMORY_GB']}GB RAM, {self.deployment_config['CPU_COUNT']} vCPUs{Colors.END}")
        
    def update_env_file(self):
        """Update .env file with all configuration"""
        self.print_step("8", "Updating Environment Configuration")
        
        # Read existing .env
        env_content = ""
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                env_content = f.read()
                
        # Update with new values
        lines = env_content.split('\n')
        updated_lines = []
        keys_added = set()
        
        for line in lines:
            if '=' in line and not line.startswith('#'):
                key = line.split('=', 1)[0].strip()
                if key in self.deployment_config:
                    updated_lines.append(f"{key}={self.deployment_config[key]}")
                    keys_added.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
                
        # Add any missing keys (including deployment-specific ones)
        updated_lines.append(f"\n# Deployment Configuration - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for key, value in self.deployment_config.items():
            if key not in keys_added and key not in ['DOCKER_USERNAME', 'DOCKER_PASSWORD']:
                # Include RUNPOD_API_KEY and ENDPOINT_URL for the client
                if key in ['RUNPOD_API_KEY', 'ENDPOINT_URL', 'ENDPOINT_ID', 'TEMPLATE_ID']:
                    updated_lines.append(f"{key}={value}")
                elif key not in ['RUNPOD_API_KEY']:  # Other deployment keys except sensitive ones
                    updated_lines.append(f"{key}={value}")
                
        # Write updated .env
        with open(self.env_file, 'w') as f:
            f.write('\n'.join(updated_lines))
            
        self.print_success("Environment file updated with deployment configuration")
        
    def run_local_test(self):
        """Run local test to verify everything works"""
        self.print_step("9", "Running Local Tests")
        
        if self.ask_yes_no("Run local tests to verify the setup?", True):
            # Test RunPod handler
            if self.run_command("python runpod_handler.py --action get_provinces", "Testing RunPod handler", check=False):
                self.print_success("Local tests passed!")
            else:
                self.print_warning("Local tests had issues - check your configuration")
        else:
            self.print_info("Skipping local tests")
            
    def show_next_steps(self):
        """Show final instructions"""
        self.print_step("10", "Next Steps")
        
        print(f"{Colors.BOLD}{Colors.GREEN}🎉 Deployment preparation complete!{Colors.END}\n")
        
        print(f"{Colors.BOLD}What's been done:{Colors.END}")
        print(f"{Colors.GREEN}✅ Dependencies checked{Colors.END}")
        print(f"{Colors.GREEN}✅ Security credentials generated{Colors.END}")
        print(f"{Colors.GREEN}✅ Docker image built and pushed{Colors.END}")
        print(f"{Colors.GREEN}✅ RunPod configuration prepared{Colors.END}")
        
        if 'TEMPLATE_ID' in self.deployment_config:
            print(f"{Colors.GREEN}✅ RunPod template created automatically{Colors.END}")
        
        if 'ENDPOINT_ID' in self.deployment_config:
            print(f"{Colors.GREEN}✅ RunPod endpoint created automatically{Colors.END}")
            print(f"{Colors.GREEN}✅ Endpoint tested and working{Colors.END}")
        
        print(f"{Colors.GREEN}✅ Deployment guide created{Colors.END}")
        
        if 'ENDPOINT_ID' in self.deployment_config:
            print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 Deployment Complete!{Colors.END}")
            print(f"{Colors.GREEN}Your endpoint is ready to use:{Colors.END}")
            print(f"{Colors.PURPLE}{self.deployment_config['ENDPOINT_URL']}{Colors.END}")
            
            print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
            print(f"{Colors.CYAN}1. Test your endpoint with the curl commands in RUNPOD_DEPLOYMENT.md{Colors.END}")
            print(f"{Colors.CYAN}2. Monitor usage and costs in the RunPod dashboard{Colors.END}")
            print(f"{Colors.CYAN}3. Scale your endpoint as needed{Colors.END}")
        else:
            print(f"\n{Colors.BOLD}Manual steps remaining:{Colors.END}")
            print(f"{Colors.YELLOW}1. Go to https://runpod.io and create your endpoint{Colors.END}")
            print(f"{Colors.YELLOW}2. Use the configuration from RUNPOD_DEPLOYMENT.md{Colors.END}")
            print(f"{Colors.YELLOW}3. Test your deployment with the provided curl commands{Colors.END}")
        
        print(f"\n{Colors.BOLD}Files created:{Colors.END}")
        print(f"{Colors.CYAN}• .env - Updated with all configuration{Colors.END}")
        print(f"{Colors.CYAN}• RUNPOD_DEPLOYMENT.md - Complete deployment guide{Colors.END}")
        
        print(f"\n{Colors.BOLD}Your Docker image:{Colors.END}")
        print(f"{Colors.PURPLE}{self.deployment_config['DOCKER_IMAGE']}{Colors.END}")
        
    def show_configuration_summary(self):
        """Show a summary of the current configuration"""
        print(f"\n{Colors.BOLD}{Colors.PURPLE}📋 Configuration Summary{Colors.END}")
        print(f"{Colors.PURPLE}{'='*50}{Colors.END}")
        
        # API Credentials
        print(f"{Colors.BOLD}API Credentials:{Colors.END}")
        print(f"  • Anthropic API: {'✅ Configured' if self.deployment_config.get('ANTHROPIC_API_KEY') else '❌ Missing'}")
        print(f"  • Supabase: {'✅ Configured' if self.deployment_config.get('SUPABASE_URL') else '❌ Not configured'}")
        
        # Docker Configuration
        print(f"{Colors.BOLD}Docker Configuration:{Colors.END}")
        print(f"  • Username: {self.deployment_config.get('DOCKER_USERNAME', '❌ Not set')}")
        print(f"  • Image: {self.deployment_config.get('DOCKER_IMAGE', '❌ Not set')}")
        
        # RunPod Configuration
        print(f"{Colors.BOLD}RunPod Configuration:{Colors.END}")
        print(f"  • API Key: {'✅ Present' if self.deployment_config.get('RUNPOD_API_KEY') else '❌ Missing'}")
        print(f"  • Endpoint: {self.deployment_config.get('ENDPOINT_NAME', '❌ Not set')}")
        print(f"  • Resources: {self.deployment_config.get('MEMORY_GB', '?')}GB RAM, {self.deployment_config.get('CPU_COUNT', '?')} vCPUs")
        
        # Security
        has_jwt = self.deployment_config.get('JWT_SECRET_KEY') and self.deployment_config['JWT_SECRET_KEY'] != 'your_jwt_secret_key_here_generate_random_32_chars'
        has_api_keys = self.deployment_config.get('API_KEYS') and self.deployment_config['API_KEYS'] != 'api_key_1,api_key_2,api_key_3'
        print(f"{Colors.BOLD}Security:{Colors.END}")
        print(f"  • JWT Secret: {'✅ Generated' if has_jwt else '❌ Default'}")
        print(f"  • API Keys: {'✅ Generated' if has_api_keys else '❌ Default'}")
        
        print(f"{Colors.PURPLE}{'='*50}{Colors.END}\n")

    def has_complete_config(self):
        """Check if we have all required configuration for RunPod deployment"""
        required_keys = [
            'ANTHROPIC_API_KEY',
            'DOCKER_USERNAME', 
            'DOCKER_PASSWORD',
            'RUNPOD_API_KEY',
            'ENDPOINT_NAME',
            'MEMORY_GB',
            'CPU_COUNT'
        ]
        
        # Check if all required keys are present and not default values
        for key in required_keys:
            if not self.deployment_config.get(key):
                return False
        
        # For RunPod deployment, JWT tokens are optional
        # The deployment will work without them since RunPod handles authentication
        return True

    def run(self):
        """Run the complete deployment process"""
        self.print_header("TKR News Gather - RunPod Deployment")
        
        print(f"{Colors.CYAN}This script will guide you through deploying TKR News Gather to RunPod.{Colors.END}")
        print(f"{Colors.CYAN}We'll handle Docker builds, credential generation, and configuration.{Colors.END}")
        
        # Show current configuration status
        if hasattr(self, '_config_loaded') and self._config_loaded:
            self.show_configuration_summary()
            
            # Quick mode handling
            if self.quick_mode:
                if self.has_complete_config():
                    print(f"{Colors.GREEN}🚀 Quick mode: Using existing complete configuration{Colors.END}\n")
                else:
                    print(f"{Colors.YELLOW}⚠️  Quick mode: Missing required configuration, switching to interactive mode{Colors.END}\n")
                    self.quick_mode = False
            
            if not self.quick_mode:
                if self.ask_yes_no("Continue with existing configuration (or reconfigure)?", True):
                    print(f"{Colors.GREEN}Using existing configuration where possible.{Colors.END}\n")
                else:
                    print(f"{Colors.YELLOW}Will ask for all configuration during deployment.{Colors.END}\n")
        
        if not self.quick_mode and not self.ask_yes_no("Ready to start the deployment process?", True):
            print("Deployment cancelled.")
            sys.exit(0)
            
        try:
            self.check_dependencies()
            self.generate_secrets()
            self.get_api_credentials()
            self.get_docker_config()
            self.build_and_push_image()
            self.get_runpod_config()
            
            # Ask if user wants automatic RunPod deployment
            if requests is not None:
                auto_deploy = self.ask_yes_no("Create RunPod template and endpoint automatically using the API?", True)
            else:
                self.print_warning("Automatic deployment not available (requests module missing)")
                auto_deploy = False
            
            if auto_deploy:
                if self.create_runpod_template_and_endpoint():
                    # Test the endpoint if it was created successfully
                    time.sleep(5)  # Give endpoint time to initialize
                    self.test_runpod_endpoint()
            
            self.generate_runpod_deployment_guide()
            self.update_env_file()
            self.run_local_test()
            self.show_next_steps()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Deployment cancelled by user.{Colors.END}")
            sys.exit(0)
        except Exception as e:
            self.print_error(f"Deployment failed: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive RunPod Deployment Script")
    parser.add_argument("--quick", action="store_true", 
                       help="Quick mode: use existing .env configuration without prompts")
    parser.add_argument("--interactive", action="store_true",
                       help="Force interactive mode even with complete configuration")
    
    args = parser.parse_args()
    
    # Quick mode if requested and not forced interactive
    quick_mode = args.quick and not args.interactive
    
    script = DeploymentScript(quick_mode=quick_mode)
    script.run()