"""
Carousel management module for the dual carousel slideshow.

This module provides carousel management functionality including:
- Day and night image collections
- Shuffle and sequential ordering
- Navigation (next, previous, jump to index)
- Resume state persistence
- Auto-reload functionality
"""

from .carousel_manager import Carousel, CarouselManager

__all__ = ['Carousel', 'CarouselManager']