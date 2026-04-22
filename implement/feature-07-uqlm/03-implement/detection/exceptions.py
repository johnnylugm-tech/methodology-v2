# detection/exceptions.py
"""Custom exceptions for Layer 3: UQLM + Activation Probes.

This module defines the exception hierarchy for the detection layer.
All exceptions inherit from DetectionError base class.

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations


class DetectionError(Exception):
    """Base exception for all detection layer errors.

    All other detection-specific exceptions inherit from this class.
    Provides error context for debugging and logging.

    Attributes:
        message: Human-readable error message
        component: Which component raised the error
        details: Additional error context dictionary
    """

    def __init__(
        self,
        message: str,
        component: str = "detection",
        details: dict | None = None,
    ) -> None:
        """Initialize DetectionError with context.

        Args:
            message: Error message describing what went wrong
            component: Name of the component that raised this error
            details: Optional dictionary with additional context
        """
        super().__init__(message)
        self.message = message
        self.component = component
        self.details = details or {}

    def __str__(self) -> str:
        """Return formatted error string with context."""
        parts = [f"[{self.component}] {self.message}"]
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class UQLMError(DetectionError):
    """Exception raised for UQLM Ensemble scoring failures.

    Raised when:
    - Model API call fails after retries
    - Network timeout occurs
    - Invalid response format from model
    - All scorers return invalid scores

    Attributes:
        model_name: Model identifier that failed
        scorer_names: List of scorers attempted
        retry_count: Number of retries attempted
    """

    def __init__(
        self,
        message: str,
        model_name: str = "",
        scorer_names: list | None = None,
        retry_count: int = 0,
        details: dict | None = None,
    ) -> None:
        """Initialize UQLMError with context.

        Args:
            message: Error message
            model_name: Model identifier that failed
            scorer_names: List of scorer names attempted
            retry_count: Number of retries before failure
            details: Additional context dictionary
        """
        super().__init__(
            message=message,
            component="UQLMEnsemble",
            details=details,
        )
        self.model_name = model_name
        self.scorer_names = scorer_names or []
        self.retry_count = retry_count

    def __str__(self) -> str:
        """Return formatted UQLM error string."""
        parts = [super().__str__()]
        if self.model_name:
            parts.append(f"Model: {self.model_name}")
        if self.scorer_names:
            parts.append(f"Scorers: {', '.join(self.scorer_names)}")
        if self.retry_count:
            parts.append(f"Retries: {self.retry_count}")
        return " | ".join(parts)


class ProbeError(DetectionError):
    """Exception raised for Activation Probe failures.

    Raised when:
    - Model type not supported
    - Invalid layer index provided
    - Probe prediction fails
    - Hidden state extraction fails

    Attributes:
        model_type: Model identifier that caused the error
        layer_idx: Layer index that was invalid
        probe_type: Type of probe being used
    """

    def __init__(
        self,
        message: str,
        model_type: str = "",
        layer_idx: int = -1,
        probe_type: str = "",
        details: dict | None = None,
    ) -> None:
        """Initialize ProbeError with context.

        Args:
            message: Error message
            model_type: Model identifier
            layer_idx: Invalid layer index
            probe_type: Type of probe being used
            details: Additional context dictionary
        """
        super().__init__(
            message=message,
            component="ActivationProbe",
            details=details,
        )
        self.model_type = model_type
        self.layer_idx = layer_idx
        self.probe_type = probe_type

    def __str__(self) -> str:
        """Return formatted Probe error string."""
        parts = [super().__str__()]
        if self.model_type:
            parts.append(f"Model: {self.model_type}")
        if self.layer_idx >= 0:
            parts.append(f"Layer: {self.layer_idx}")
        if self.probe_type:
            parts.append(f"Probe: {self.probe_type}")
        return " | ".join(parts)


class DataInsufficientError(DetectionError):
    """Exception raised for insufficient training data.

    Raised when:
    - Training data has fewer than required samples
    - Labels are all the same class (no variation)
    - Hidden states have mismatched dimensions

    Attributes:
        provided_count: Number of samples provided
        required_count: Minimum number of samples required
        data_type: Type of data that was insufficient
    """

    def __init__(
        self,
        message: str,
        provided_count: int = 0,
        required_count: int = 10,
        data_type: str = "training",
        details: dict | None = None,
    ) -> None:
        """Initialize DataInsufficientError with context.

        Args:
            message: Error message
            provided_count: Number of samples actually provided
            required_count: Minimum samples required
            data_type: Type of data (training, validation, etc.)
            details: Additional context dictionary
        """
        super().__init__(
            message=message,
            component="DataValidation",
            details=details,
        )
        self.provided_count = provided_count
        self.required_count = required_count
        self.data_type = data_type

    def __str__(self) -> str:
        """Return formatted DataInsufficient error string."""
        parts = [super().__str__()]
        parts.append(f"Provided: {self.provided_count} {self.data_type} samples")
        parts.append(f"Required: {self.required_count}")
        return " | ".join(parts)


class BaselineNotFoundError(DetectionError):
    """Exception raised when baseline distribution is not initialized.

    Raised when:
    - MetaQA drift detection attempted without baseline
    - First-run baseline not yet established
    - Baseline was cleared but not rebuilt

    Attributes:
        baseline_version: Version of baseline that was missing
        window_size: Window size that was used
    """

    def __init__(
        self,
        message: str,
        baseline_version: str = "",
        window_size: int = 0,
        details: dict | None = None,
    ) -> None:
        """Initialize BaselineNotFoundError with context.

        Args:
            message: Error message
            baseline_version: Version identifier of missing baseline
            window_size: Window size context
            details: Additional context dictionary
        """
        super().__init__(
            message=message,
            component="MetaQA",
            details=details,
        )
        self.baseline_version = baseline_version
        self.window_size = window_size

    def __str__(self) -> str:
        """Return formatted BaselineNotFound error string."""
        parts = [super().__str__()]
        if self.baseline_version:
            parts.append(f"Baseline: {self.baseline_version}")
        if self.window_size > 0:
            parts.append(f"Window: {self.window_size}")
        return " | ".join(parts)


class CalibrationError(DetectionError):
    """Exception raised for Confidence Calibration failures.

    Raised when:
    - Invalid confidence value (outside [0, 1])
    - Invalid outcome value
    - Calibration history is corrupted
    - Platt scaling computation fails

    Attributes:
        confidence_value: The invalid confidence value
        outcome_value: The invalid outcome value
    """

    def __init__(
        self,
        message: str,
        confidence_value: float = -1.0,
        outcome_value: bool = False,
        details: dict | None = None,
    ) -> None:
        """Initialize CalibrationError with context.

        Args:
            message: Error message
            confidence_value: Invalid confidence value
            outcome_value: Invalid outcome value
            details: Additional context dictionary
        """
        super().__init__(
            message=message,
            component="Calibration",
            details=details,
        )
        self.confidence_value = confidence_value
        self.outcome_value = outcome_value

    def __str__(self) -> str:
        """Return formatted Calibration error string."""
        parts = [super().__str__()]
        if self.confidence_value >= 0:
            parts.append(f"Confidence: {self.confidence_value}")
        return " | ".join(parts)


class GapDetectionError(DetectionError):
    """Exception raised for Gap Detection failures.

    Raised when:
    - Source code has syntax errors
    - File cannot be read
    - AST parsing fails
    - Invalid gap types specified

    Attributes:
        file_path: File path where error occurred
        line_number: Line number where error occurred
        error_type: Type of error (syntax, io, parse)
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        line_number: int = 0,
        error_type: str = "",
        details: dict | None = None,
    ) -> None:
        """Initialize GapDetectionError with context.

        Args:
            message: Error message
            file_path: File where error occurred
            line_number: Line number where error occurred
            error_type: Type of error encountered
            details: Additional context dictionary
        """
        super().__init__(
            message=message,
            component="GapDetector",
            details=details,
        )
        self.file_path = file_path
        self.line_number = line_number
        self.error_type = error_type

    def __str__(self) -> str:
        """Return formatted GapDetection error string."""
        parts = [super().__str__()]
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.line_number > 0:
            parts.append(f"Line: {self.line_number}")
        if self.error_type:
            parts.append(f"Type: {self.error_type}")
        return " | ".join(parts)


class InsufficientDataError(DetectionError):
    """Exception raised when combined uncertainty data is insufficient.

    Raised when:
    - All three components (UQLM, CLAP, MetaQA) are missing
    - No valid scores can be computed
    - Required inputs not provided

    Attributes:
        missing_components: List of missing component names
        provided_components: List of provided component names
    """

    def __init__(
        self,
        message: str,
        missing_components: list | None = None,
        provided_components: list | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize InsufficientDataError with context.

        Args:
            message: Error message
            missing_components: Components that were not provided
            provided_components: Components that were provided
            details: Additional context dictionary
        """
        super().__init__(
            message=message,
            component="UncertaintyScore",
            details=details,
        )
        self.missing_components = missing_components or []
        self.provided_components = provided_components or []

    def __str__(self) -> str:
        """Return formatted InsufficientData error string."""
        parts = [super().__str__()]
        if self.missing_components:
            parts.append(f"Missing: {', '.join(self.missing_components)}")
        return " | ".join(parts)


# =============================================================================
# Exception Grouping for Catch-All Handling
# =============================================================================

# Alias for catching all detection errors
DetectionLayerError = DetectionError
