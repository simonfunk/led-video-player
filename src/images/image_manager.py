"""
Image processing and management system for the dual carousel slideshow.

This module handles:
- Image file discovery and filtering by supported formats
- EXIF orientation processing using Pillow
- Image scaling functionality for cover and fit modes
- Image caching system with preloading
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from threading import Lock, Thread
from queue import Queue
import time
from datetime import datetime

import pygame
from PIL import Image, ImageOps, ExifTags

from error_handling.error_handler import (
    handle_image_error, handle_folder_error, error_handler, 
    ErrorCategory, ErrorInfo, ErrorSeverity
)


logger = logging.getLogger(__name__)


class ImageManager:
    """Manages image loading, processing, caching, and scaling."""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    def __init__(self, cache_size: int = 50):
        """
        Initialize the ImageManager.
        
        Args:
            cache_size: Maximum number of processed images to keep in cache
        """
        self.cache_size = cache_size
        self._image_cache: Dict[str, pygame.Surface] = {}
        self._cache_lock = Lock()
        self._preload_queue = Queue()
        self._preload_thread: Optional[Thread] = None
        self._preload_running = False
        
        # Initialize pygame for surface operations
        if not pygame.get_init():
            pygame.init()
    
    def scan_folder(self, folder_path: str, include_subfolders: bool = True) -> List[str]:
        """
        Scan a folder for supported image files with comprehensive error handling.
        
        Args:
            folder_path: Path to the folder to scan
            include_subfolders: Whether to include subfolders in the scan
            
        Returns:
            List of image file paths sorted alphabetically
        """
        if not os.path.exists(folder_path):
            error_info = ErrorInfo(
                category=ErrorCategory.FOLDER_ACCESS,
                severity=ErrorSeverity.MEDIUM,
                message=f"Folder does not exist: {folder_path}",
                context={'folder_path': folder_path, 'operation': 'scan_folder'}
            )
            error_handler.handle_error(error_info)
            return []
        
        # Use retry logic for folder scanning
        success, result = error_handler.retry_operation(
            self._scan_folder_internal, 
            ErrorCategory.FOLDER_ACCESS,
            folder_path, include_subfolders
        )
        
        if success:
            logger.info(f"Found {len(result)} images in {folder_path}")
            return result
        else:
            logger.error(f"Failed to scan folder {folder_path} after retries")
            return []
    
    def _scan_folder_internal(self, folder_path: str, include_subfolders: bool) -> List[str]:
        """Internal folder scanning implementation."""
        image_paths = []
        folder = Path(folder_path)
        corrupted_files = []
        
        try:
            if include_subfolders:
                # Recursively scan all subdirectories
                for file_path in folder.rglob('*'):
                    if file_path.is_file() and self._is_supported_format(file_path):
                        if self._validate_image_file_quick(file_path):
                            image_paths.append(str(file_path))
                        else:
                            corrupted_files.append(str(file_path))
            else:
                # Scan only the immediate directory
                for file_path in folder.iterdir():
                    if file_path.is_file() and self._is_supported_format(file_path):
                        if self._validate_image_file_quick(file_path):
                            image_paths.append(str(file_path))
                        else:
                            corrupted_files.append(str(file_path))
            
            # Log corrupted files found during scan
            if corrupted_files:
                logger.warning(f"Found {len(corrupted_files)} corrupted/unreadable files in {folder_path}")
                for corrupted_file in corrupted_files[:5]:  # Log first 5
                    logger.debug(f"Corrupted file: {corrupted_file}")
                if len(corrupted_files) > 5:
                    logger.debug(f"... and {len(corrupted_files) - 5} more corrupted files")
            
            # Sort alphabetically for consistent ordering
            image_paths.sort()
            
        except PermissionError as e:
            raise Exception(f"Permission denied accessing folder {folder_path}: {e}")
        except OSError as e:
            raise Exception(f"OS error scanning folder {folder_path}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error scanning folder {folder_path}: {e}")
        
        return image_paths
    
    def _validate_image_file_quick(self, file_path: Path) -> bool:
        """
        Quick validation of image file without full loading.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            bool: True if file appears to be a valid image
        """
        try:
            # Check file size (skip empty files)
            if file_path.stat().st_size == 0:
                return False
            
            # Try to open and verify it's an image
            with Image.open(file_path) as img:
                # Just verify the image header, don't load pixel data
                img.verify()
                return True
                
        except Exception:
            # Any exception means the file is not a valid image
            return False
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if a file has a supported image format."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """
        Load an image from disk and process EXIF orientation with error handling.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            PIL Image object with correct orientation, or None if loading failed
        """
        try:
            # Check if file exists and is readable
            if not os.path.exists(image_path):
                handle_image_error(image_path, FileNotFoundError(f"Image file not found: {image_path}"))
                return None
            
            # Check file size
            try:
                file_size = os.path.getsize(image_path)
                if file_size == 0:
                    handle_image_error(image_path, ValueError("Image file is empty"))
                    return None
                elif file_size > 100 * 1024 * 1024:  # 100MB limit
                    logger.warning(f"Large image file ({file_size / 1024 / 1024:.1f}MB): {image_path}")
            except OSError as e:
                handle_image_error(image_path, e)
                return None
            
            # Use retry logic for image loading
            success, result = error_handler.retry_operation(
                self._load_image_internal,
                ErrorCategory.IMAGE_LOADING,
                image_path
            )
            
            if success:
                return result
            else:
                handle_image_error(image_path, Exception("Failed to load after retries"))
                return None
                
        except Exception as e:
            handle_image_error(image_path, e)
            return None
    
    def _load_image_internal(self, image_path: str) -> Image.Image:
        """Internal image loading implementation."""
        try:
            with Image.open(image_path) as img:
                # Verify the image is valid
                img.verify()
                
            # Reopen for actual processing (verify() closes the file)
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (handles RGBA, P, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Process EXIF orientation
                img = self._process_exif_orientation(img)
                
                # Create a copy since we're using 'with' statement
                return img.copy()
                
        except (IOError, OSError) as e:
            raise Exception(f"IO error loading image {image_path}: {e}")
        except Image.DecompressionBombError as e:
            raise Exception(f"Image too large (decompression bomb): {image_path}")
        except Exception as e:
            raise Exception(f"Unexpected error loading image {image_path}: {e}")
    
    def _process_exif_orientation(self, image: Image.Image) -> Image.Image:
        """
        Process EXIF orientation data to correctly orient the image.
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image object with correct orientation
        """
        try:
            # Get EXIF data
            exif = image.getexif()
            
            if exif is not None:
                # Look for orientation tag (274 is the EXIF orientation tag)
                orientation = exif.get(274)
                
                if orientation:
                    # Apply the appropriate transformation
                    if orientation == 2:
                        # Horizontal flip
                        image = image.transpose(Image.FLIP_LEFT_RIGHT)
                    elif orientation == 3:
                        # 180 degree rotation
                        image = image.rotate(180, expand=True)
                    elif orientation == 4:
                        # Vertical flip
                        image = image.transpose(Image.FLIP_TOP_BOTTOM)
                    elif orientation == 5:
                        # Horizontal flip + 90 degree rotation
                        image = image.transpose(Image.FLIP_LEFT_RIGHT)
                        image = image.rotate(90, expand=True)
                    elif orientation == 6:
                        # 90 degree rotation
                        image = image.rotate(270, expand=True)
                    elif orientation == 7:
                        # Horizontal flip + 270 degree rotation
                        image = image.transpose(Image.FLIP_LEFT_RIGHT)
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        # 270 degree rotation
                        image = image.rotate(90, expand=True)
                        
        except Exception as e:
            logger.debug(f"Could not process EXIF orientation: {e}")
        
        return image
    
    def scale_image(self, image: Image.Image, target_size: Tuple[int, int], 
                   fit_mode: str = "cover") -> pygame.Surface:
        """
        Scale an image to fit the target size using the specified fit mode.
        
        Args:
            image: PIL Image object to scale
            target_size: Target (width, height) tuple
            fit_mode: "cover" to fill screen (may crop), "fit" to fit entirely (may have bars)
            
        Returns:
            pygame Surface with the scaled image
        """
        target_width, target_height = target_size
        img_width, img_height = image.size
        
        # Calculate scaling ratios
        width_ratio = target_width / img_width
        height_ratio = target_height / img_height
        
        if fit_mode.lower() == "cover":
            # Scale to fill the entire target area (may crop)
            scale_ratio = max(width_ratio, height_ratio)
        else:  # fit mode
            # Scale to fit entirely within target area (may have bars)
            scale_ratio = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(img_width * scale_ratio)
        new_height = int(img_height * scale_ratio)
        
        # Resize the image
        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert PIL image to pygame surface
        mode = scaled_image.mode
        size = scaled_image.size
        data = scaled_image.tobytes()
        
        pygame_surface = pygame.image.fromstring(data, size, mode)
        
        return pygame_surface
    
    def get_cached_image(self, image_path: str, target_size: Tuple[int, int], 
                        fit_mode: str = "cover") -> Optional[pygame.Surface]:
        """
        Get a cached processed image or load and cache it if not available.
        
        Args:
            image_path: Path to the image file
            target_size: Target (width, height) tuple
            fit_mode: "cover" or "fit" mode
            
        Returns:
            pygame Surface with the processed image, or None if loading failed
        """
        # Create cache key including size and fit mode
        cache_key = f"{image_path}_{target_size[0]}x{target_size[1]}_{fit_mode}"
        
        with self._cache_lock:
            # Check if image is already cached
            if cache_key in self._image_cache:
                logger.debug(f"Cache hit for {image_path}")
                return self._image_cache[cache_key]
        
        try:
            # Load and process the image with error handling
            pil_image = self.load_image(image_path)
            if pil_image is None:
                return None
            
            # Scale the image with error handling
            pygame_surface = self._scale_image_safe(pil_image, target_size, fit_mode, image_path)
            if pygame_surface is None:
                return None
            
            # Cache the processed image
            with self._cache_lock:
                try:
                    # Remove oldest items if cache is full
                    if len(self._image_cache) >= self.cache_size:
                        # Remove the first item (oldest)
                        oldest_key = next(iter(self._image_cache))
                        del self._image_cache[oldest_key]
                        logger.debug(f"Removed {oldest_key} from cache")
                    
                    self._image_cache[cache_key] = pygame_surface
                    logger.debug(f"Cached {cache_key}")
                    
                except Exception as e:
                    logger.warning(f"Failed to cache image {image_path}: {e}")
                    # Continue without caching
            
            return pygame_surface
            
        except Exception as e:
            handle_image_error(image_path, e)
            return None
    
    def _scale_image_safe(self, image: Image.Image, target_size: Tuple[int, int], 
                         fit_mode: str, image_path: str) -> Optional[pygame.Surface]:
        """
        Safely scale an image with error handling.
        
        Args:
            image: PIL Image object to scale
            target_size: Target (width, height) tuple
            fit_mode: "cover" or "fit" mode
            image_path: Path for error reporting
            
        Returns:
            pygame Surface with the scaled image, or None if scaling failed
        """
        try:
            return self.scale_image(image, target_size, fit_mode)
        except MemoryError as e:
            handle_image_error(image_path, Exception(f"Out of memory scaling image: {e}"))
            return None
        except Exception as e:
            handle_image_error(image_path, Exception(f"Error scaling image: {e}"))
            return None
    
    def preload_images(self, image_paths: List[str], target_size: Tuple[int, int], 
                      fit_mode: str = "cover", max_preload: int = 5):
        """
        Preload images in the background for better performance.
        
        Args:
            image_paths: List of image paths to preload
            target_size: Target (width, height) tuple
            fit_mode: "cover" or "fit" mode
            max_preload: Maximum number of images to preload
        """
        if not image_paths:
            return
        
        # Stop any existing preload operation
        self.stop_preloading()
        
        # Add images to preload queue (limit to max_preload)
        for i, image_path in enumerate(image_paths[:max_preload]):
            self._preload_queue.put((image_path, target_size, fit_mode))
        
        # Start preload thread
        self._preload_running = True
        self._preload_thread = Thread(target=self._preload_worker, daemon=True)
        self._preload_thread.start()
        
        logger.info(f"Started preloading {min(len(image_paths), max_preload)} images")
    
    def _preload_worker(self):
        """Background worker for preloading images."""
        while self._preload_running:
            try:
                # Get next item from queue (with timeout to allow checking _preload_running)
                try:
                    image_path, target_size, fit_mode = self._preload_queue.get(timeout=1.0)
                except:
                    continue
                
                # Preload the image (this will cache it)
                self.get_cached_image(image_path, target_size, fit_mode)
                
                # Mark task as done
                self._preload_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in preload worker: {e}")
    
    def stop_preloading(self):
        """Stop the background preloading operation."""
        if self._preload_running:
            self._preload_running = False
            if self._preload_thread and self._preload_thread.is_alive():
                self._preload_thread.join(timeout=2.0)
            logger.debug("Stopped preloading")
    
    def clear_cache(self):
        """Clear the image cache."""
        with self._cache_lock:
            self._image_cache.clear()
            logger.info("Cleared image cache")
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get information about the current cache state."""
        with self._cache_lock:
            return {
                'cached_images': len(self._image_cache),
                'cache_size_limit': self.cache_size,
                'preload_queue_size': self._preload_queue.qsize()
            }
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_preloading()
        self.clear_cache()
        logger.info("ImageManager cleanup completed")


class ImageProcessor:
    """Utility class for image processing operations."""
    
    @staticmethod
    def get_image_info(image_path: str) -> Optional[Dict]:
        """
        Get basic information about an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image info or None if file cannot be read
        """
        try:
            with Image.open(image_path) as img:
                info = {
                    'path': image_path,
                    'size': img.size,
                    'mode': img.mode,
                    'format': img.format,
                    'has_exif': bool(img.getexif()),
                    'file_size': os.path.getsize(image_path)
                }
                return info
        except Exception as e:
            logger.error(f"Could not get info for {image_path}: {e}")
            return None
    
    @staticmethod
    def validate_image_file(image_path: str) -> bool:
        """
        Validate that an image file can be loaded and processed.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if the image is valid and can be processed
        """
        try:
            with Image.open(image_path) as img:
                # Try to load the image data
                img.load()
                return True
        except Exception as e:
            logger.debug(f"Image validation failed for {image_path}: {e}")
            return False