# Model Configuration
VISION_MODEL = "gpt-4o"  # Model for processing images and text pages
CLEANUP_MODEL = "gpt-4o-mini"  # Model for final document cleanup
TEMPERATURE = 0.0  # Temperature setting for all API calls
MAX_TOKENS = 4096  # Maximum tokens for API responses

# Token Estimation Configuration
CHARS_PER_TOKEN = 4  # Rough estimate for token calculation
IMAGE_TOKEN_BASE = {
    "high": 525,  # Base tokens for high detail image
    "standard": 150  # Base tokens for standard detail image
}
IMAGE_TOKEN_MULTIPLIER = 1.75  # Adjustment factor for image token estimation
TEXT_TOKEN_REDUCTION = 0.85  # Reduction factor for text token estimation

# Page Processing Configuration
IMAGE_AREA_THRESHOLD = 0.1  # Threshold for determining text-only pages (10% of page area)

# File Paths
DATA_DIR = "data"  # Directory for PDF and markdown files

# API Configuration
MAX_RETRIES = 3  # Maximum number of API call retries
RETRY_DELAY = 1  # Delay between retries in seconds 