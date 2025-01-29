"""
Token Estimation Module
Provides functionality for estimating token usage in API calls.
"""

from config import (
    CHARS_PER_TOKEN,
    IMAGE_TOKEN_BASE,
    IMAGE_TOKEN_MULTIPLIER,
    TEXT_TOKEN_REDUCTION
)

class TokenEstimator:
    """Handles token estimation for different types of content"""
    
    @staticmethod
    def estimate_from_string(text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        Uses character count as a rough approximation.
        
        Args:
            text (str): The text to estimate tokens for
            
        Returns:
            int: Estimated number of tokens
        """
        return len(text) // CHARS_PER_TOKEN
    
    @staticmethod
    def estimate_image_tokens(detail: str = "high") -> int:
        """
        Estimate tokens for image processing.
        Includes base image tokens and adjustment factor.
        
        Args:
            detail (str): Detail level, either 'high' or 'standard'
            
        Returns:
            int: Estimated number of tokens
        """
        base_tokens = IMAGE_TOKEN_BASE.get(detail, IMAGE_TOKEN_BASE["standard"])
        return int(base_tokens * IMAGE_TOKEN_MULTIPLIER)
    
    @staticmethod
    def estimate_text_processing(text: str) -> int:
        """
        Estimate tokens for text processing with reduction factor.
        
        Args:
            text (str): The text to process
            
        Returns:
            int: Estimated number of tokens
        """
        base_estimate = TokenEstimator.estimate_from_string(text)
        return int(base_estimate * TEXT_TOKEN_REDUCTION)
    
    @staticmethod
    def calculate_token_difference(estimated: int, actual: int) -> tuple[float, int]:
        """
        Calculate the difference between estimated and actual tokens.
        
        Args:
            estimated (int): Estimated token count
            actual (int): Actual token count
            
        Returns:
            tuple[float, int]: Percentage difference and absolute difference
        """
        if estimated <= 0:
            return 0.0, 0
            
        diff_percent = ((actual - estimated) / estimated * 100)
        diff_absolute = actual - estimated
        return diff_percent, diff_absolute
    
    @staticmethod
    def format_token_stats(estimated: int, actual: int) -> dict[str, str]:
        """
        Format token statistics for display.
        
        Args:
            estimated (int): Estimated token count
            actual (int): Actual token count
            
        Returns:
            dict[str, str]: Formatted statistics
        """
        diff_percent, diff_absolute = TokenEstimator.calculate_token_difference(estimated, actual)
        return {
            "estimated": f"{estimated:,}",
            "actual": f"{actual:,}",
            "difference": f"{diff_percent:+.1f}% ({diff_absolute:+,} tokens)"
        } 