"""
Dependency validation utilities to check for required libraries and provide helpful error messages.
"""
import sys
import logging
import importlib
from typing import Dict, List, Any, Optional
from pathlib import Path


class DependencyValidator:
    """Validates that all required dependencies are available and provides helpful error messages."""
    
    # Required dependencies with minimum versions and installation instructions
    REQUIRED_DEPENDENCIES = {
        'pygame': {
            'min_version': '2.5.0',
            'import_name': 'pygame',
            'install_cmd': 'pip install pygame>=2.5.0',
            'description': 'Cross-platform multimedia library for window management and rendering',
            'critical': True
        },
        'PIL': {
            'min_version': '10.0.0',
            'import_name': 'PIL',
            'install_cmd': 'pip install Pillow>=10.0.0',
            'description': 'Python Imaging Library for image processing and EXIF handling',
            'critical': True
        },
        'yaml': {
            'min_version': '6.0',
            'import_name': 'yaml',
            'install_cmd': 'pip install PyYAML>=6.0',
            'description': 'YAML parser for configuration file support',
            'critical': True
        },
        'astral': {
            'min_version': '3.2',
            'import_name': 'astral',
            'install_cmd': 'pip install astral>=3.2',
            'description': 'Astronomical calculations for sunrise/sunset scheduling',
            'critical': False  # Only needed for sun schedule mode
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_dependencies(self, check_optional: bool = True) -> Dict[str, Any]:
        """
        Validate all required dependencies.
        
        Args:
            check_optional: Whether to check optional dependencies
            
        Returns:
            Dict containing validation results and installation instructions
        """
        result = {
            'all_critical_available': True,
            'all_optional_available': True,
            'missing_critical': [],
            'missing_optional': [],
            'available': [],
            'version_warnings': [],
            'installation_instructions': []
        }
        
        for dep_name, dep_info in self.REQUIRED_DEPENDENCIES.items():
            is_critical = dep_info['critical']
            
            # Skip optional dependencies if not requested
            if not is_critical and not check_optional:
                continue
            
            validation = self._validate_single_dependency(dep_name, dep_info)
            
            if validation['available']:
                result['available'].append({
                    'name': dep_name,
                    'version': validation.get('version'),
                    'critical': is_critical
                })
                
                if validation.get('version_warning'):
                    result['version_warnings'].append(validation['version_warning'])
            else:
                missing_info = {
                    'name': dep_name,
                    'description': dep_info['description'],
                    'install_cmd': dep_info['install_cmd'],
                    'critical': is_critical
                }
                
                if is_critical:
                    result['missing_critical'].append(missing_info)
                    result['all_critical_available'] = False
                else:
                    result['missing_optional'].append(missing_info)
                    result['all_optional_available'] = False
        
        # Generate installation instructions
        result['installation_instructions'] = self._generate_installation_instructions(result)
        
        return result
    
    def _validate_single_dependency(self, dep_name: str, dep_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single dependency."""
        result = {
            'available': False,
            'version': None,
            'version_warning': None
        }
        
        try:
            # Try to import the module
            module = importlib.import_module(dep_info['import_name'])
            result['available'] = True
            
            # Try to get version information
            version = self._get_module_version(module, dep_name)
            if version:
                result['version'] = version
                
                # Check version compatibility (basic string comparison)
                min_version = dep_info['min_version']
                if self._is_version_older(version, min_version):
                    result['version_warning'] = (
                        f"{dep_name} version {version} is older than recommended {min_version}. "
                        f"Consider upgrading with: {dep_info['install_cmd']}"
                    )
            
            self.logger.debug(f"Dependency {dep_name} is available (version: {version or 'unknown'})")
            
        except ImportError as e:
            self.logger.warning(f"Dependency {dep_name} is not available: {e}")
        except Exception as e:
            self.logger.error(f"Error checking dependency {dep_name}: {e}")
        
        return result
    
    def _get_module_version(self, module: Any, dep_name: str) -> Optional[str]:
        """Get version information from a module."""
        version_attrs = ['__version__', 'version', 'VERSION']
        
        for attr in version_attrs:
            if hasattr(module, attr):
                version = getattr(module, attr)
                if isinstance(version, str):
                    return version
                elif hasattr(version, '__str__'):
                    return str(version)
        
        # Special cases for specific modules
        if dep_name == 'PIL':
            try:
                from PIL import __version__
                return __version__
            except ImportError:
                pass
        
        return None
    
    def _is_version_older(self, current: str, minimum: str) -> bool:
        """Simple version comparison (works for most semantic versions)."""
        try:
            current_parts = [int(x) for x in current.split('.')]
            minimum_parts = [int(x) for x in minimum.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(current_parts), len(minimum_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            minimum_parts.extend([0] * (max_len - len(minimum_parts)))
            
            return current_parts < minimum_parts
        except (ValueError, AttributeError):
            # If version parsing fails, assume it's fine
            return False
    
    def _generate_installation_instructions(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate helpful installation instructions."""
        instructions = []
        
        if validation_result['missing_critical']:
            instructions.append("CRITICAL DEPENDENCIES MISSING:")
            instructions.append("The following dependencies are required for the application to run:")
            instructions.append("")
            
            for dep in validation_result['missing_critical']:
                instructions.append(f"• {dep['name']}: {dep['description']}")
                instructions.append(f"  Install with: {dep['install_cmd']}")
                instructions.append("")
            
            instructions.append("To install all critical dependencies at once:")
            instructions.append("  pip install -r requirements.txt")
            instructions.append("")
        
        if validation_result['missing_optional']:
            instructions.append("OPTIONAL DEPENDENCIES MISSING:")
            instructions.append("The following dependencies provide additional functionality:")
            instructions.append("")
            
            for dep in validation_result['missing_optional']:
                instructions.append(f"• {dep['name']}: {dep['description']}")
                instructions.append(f"  Install with: {dep['install_cmd']}")
                instructions.append("")
        
        if validation_result['version_warnings']:
            instructions.append("VERSION WARNINGS:")
            for warning in validation_result['version_warnings']:
                instructions.append(f"• {warning}")
            instructions.append("")
        
        # Add platform-specific installation notes
        instructions.extend(self._get_platform_specific_instructions())
        
        return instructions
    
    def _get_platform_specific_instructions(self) -> List[str]:
        """Get platform-specific installation instructions."""
        instructions = []
        
        if sys.platform == 'win32':
            instructions.extend([
                "WINDOWS INSTALLATION NOTES:",
                "• Ensure Python 3.8+ is installed from python.org",
                "• Use Command Prompt or PowerShell (not Windows Store Python)",
                "• If pip is not available, install it with: python -m ensurepip --upgrade",
                ""
            ])
        elif sys.platform == 'darwin':
            instructions.extend([
                "MACOS INSTALLATION NOTES:",
                "• Ensure Python 3.8+ is installed (use Homebrew: brew install python)",
                "• You may need to install Xcode Command Line Tools: xcode-select --install",
                "• For pygame on Apple Silicon, you may need: pip install pygame --pre",
                ""
            ])
        elif sys.platform.startswith('linux'):
            instructions.extend([
                "LINUX INSTALLATION NOTES:",
                "• Ensure Python 3.8+ and pip are installed",
                "• You may need system packages: sudo apt-get install python3-dev python3-pip",
                "• For pygame: sudo apt-get install python3-pygame (or use pip)",
                ""
            ])
        
        return instructions
    
    def log_dependency_status(self, validation_result: Dict[str, Any]) -> None:
        """Log dependency validation results."""
        if not validation_result['all_critical_available']:
            self.logger.error("DEPENDENCY ERROR: Critical dependencies are missing")
            for instruction in validation_result['installation_instructions']:
                if instruction.strip():
                    self.logger.error(f"  {instruction}")
        elif not validation_result['all_optional_available']:
            self.logger.warning("Some optional dependencies are missing")
            for dep in validation_result['missing_optional']:
                self.logger.warning(f"  - {dep['name']}: {dep['description']}")
        else:
            self.logger.info("All dependencies are available")
            
        # Log version warnings
        for warning in validation_result['version_warnings']:
            self.logger.warning(f"Version warning: {warning}")
    
    def check_requirements_file(self) -> bool:
        """Check if requirements.txt exists and is readable."""
        try:
            req_file = Path(__file__).parent.parent.parent / 'requirements.txt'
            if req_file.exists():
                self.logger.info(f"Requirements file found: {req_file}")
                return True
            else:
                self.logger.warning(f"Requirements file not found: {req_file}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking requirements file: {e}")
            return False