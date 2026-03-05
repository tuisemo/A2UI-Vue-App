"""
Error Handler Service - Centralized error handling and degradation strategies
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorHandler:
    """Centralized error handling with degradation strategies"""
    
    # Error codes
    ERR_LLM_TIMEOUT = "LLM_001"
    ERR_LLM_RATE_LIMIT = "LLM_002"
    ERR_INVALID_COMPONENT = "UI_001"
    ERR_CONVERSATION_NOT_FOUND = "CONV_001"
    ERR_UNKNOWN = "UNK_001"
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.circuit_breaker_open = False
        self.failure_threshold = 5
        self.recovery_timeout = 60
        logger.info("Initialized ErrorHandler")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle error and return appropriate response
        
        Returns error response with severity and suggested action
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Determine error severity and response
        if isinstance(error, TimeoutError) or "timeout" in error_msg.lower():
            severity = ErrorSeverity.HIGH
            error_code = self.ERR_LLM_TIMEOUT
            user_message = "Service temporarily unavailable. Please try again."
            retry_recommended = True
        elif "rate limit" in error_msg.lower():
            severity = ErrorSeverity.MEDIUM
            error_code = self.ERR_LLM_RATE_LIMIT
            user_message = "Too many requests. Please wait a moment."
            retry_recommended = True
        elif isinstance(error, ValueError):
            severity = ErrorSeverity.LOW
            error_code = self.ERR_INVALID_COMPONENT
            user_message = "Invalid request format."
            retry_recommended = False
        else:
            severity = ErrorSeverity.MEDIUM
            error_code = self.ERR_UNKNOWN
            user_message = "An unexpected error occurred."
            retry_recommended = False
        
        # Log error
        logger.error(
            f"Error [{error_code}] ({severity.value}): {error_msg}",
            extra={"context": context}
        )
        
        # Track error count for circuit breaker
        self._track_error(error_code)
        
        # Check if circuit breaker should trip
        if self._should_trip_circuit_breaker(error_code):
            logger.critical("Circuit breaker tripped! Service temporarily disabled.")
        
        return {
            "error": True,
            "error_code": error_code,
            "error_type": error_type,
            "message": error_msg,
            "user_message": user_message,
            "severity": severity.value,
            "retry_recommended": retry_recommended,
            "circuit_breaker_open": self.circuit_breaker_open,
        }
    
    def _track_error(self, error_code: str):
        """Track error count for circuit breaker pattern"""
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
    
    def _should_trip_circuit_breaker(self, error_code: str) -> bool:
        """Check if circuit breaker should trip"""
        count = self.error_counts.get(error_code, 0)
        if count >= self.failure_threshold:
            self.circuit_breaker_open = True
            return True
        return False
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker after recovery"""
        self.circuit_breaker_open = False
        self.error_counts.clear()
        logger.info("Circuit breaker reset")
    
    def get_error_ui(self, error_response: Dict[str, Any]) -> Dict:
        """Generate error UI component"""
        return {
            "surfaceUpdate": {
                "surfaceId": "main",
                "components": [
                    {
                        "id": "error_alert",
                        "component": {
                            "Alert": {
                                "title": {"literalString": "Error"},
                                "message": {"literalString": error_response.get("user_message", "Unknown error")},
                                "variant": "error",
                            }
                        },
                    },
                    {
                        "id": "root",
                        "component": {
                            "Column": {
                                "children": {"explicitList": ["error_alert"]}
                            }
                        },
                    },
                ],
            },
            "beginRendering": {
                "surfaceId": "main",
                "root": "root"
            }
        }


# Singleton instance
error_handler = ErrorHandler()
