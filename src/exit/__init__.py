"""
Exit management modules - Handle position closing logic
"""

from .exit_manager import ExitManager
from .dead_trade_detector import DeadTradeDetector
from .sl_tp_manager import SLTPManager

__all__ = ['ExitManager', 'DeadTradeDetector', 'SLTPManager']
