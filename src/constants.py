"""
TRAD Bot Constants - Centralized configuration values
"""

# ============================================================================
# DEAD TRADE DETECTION THRESHOLDS
# ============================================================================

# Price movement threshold for detecting dead trades (%)
DEAD_PRICE_THRESHOLD_PCT = 0.5

# Volume ratio threshold for detecting dead trades
DEAD_VOLUME_RATIO = 0.5

# Number of candles to observe before marking trade as dead (price)
DEAD_PRICE_COUNTER_MAX = 3

# Number of candles to observe before marking trade as dead (volume)
DEAD_VOLUME_COUNTER_MAX = 3

# ============================================================================
# TRAILING STOP CONFIGURATION
# ============================================================================

# Trailing stop percentage (moves with price)
TRAILING_STOP_PCT = 0.01  # 1% trail

# ============================================================================
# POSITION MANAGEMENT
# ============================================================================

# Minimum time between trades (seconds)
TRADE_COOLDOWN_SECONDS = 300  # 5 minutes

# Take profit partial fill percentage
TP_PARTIAL_FILL = 0.5  # 50% of position

# ============================================================================
# RISK MANAGEMENT
# ============================================================================

# Maximum daily loss percentage
MAX_DAILY_LOSS_PCT = 2.0

# Maximum open positions allowed
MAX_OPEN_POSITIONS = 3

# ============================================================================
# API CONFIGURATION
# ============================================================================

# Cache duration for GatekeeperV2 decisions (seconds)
GATEKEEPER_CACHE_SECONDS = 30

# ============================================================================
# LOGGING
# ============================================================================

# Log file rotation size (bytes)
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

# Keep last N log files
LOG_BACKUP_COUNT = 5
