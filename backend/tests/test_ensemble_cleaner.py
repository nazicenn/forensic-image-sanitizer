import pytest
import numpy as np
from app.services.forensic_cleaner import EnsembleCleaner


class TestEnsembleCleaner:
    """Test EnsembleCleaner class."""

    def setup_method(self):
        self.cleaner = EnsembleCleaner()

    def test_cleaner_init(self):
        """Test EnsembleCleaner initialization."""
        assert self.cleaner is not None
        assert len(self.cleaner.detectors) == 9
        assert len(self.cleaner.strategy_weights) > 0

    def test_clean_all(self):
        """Test ensemble evasion."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.cleaner.clean_all(image, iterations=3)

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_detect_vulnerabilities(self):
        """Test vulnerability detection."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        vulnerabilities = self.cleaner._detect_vulnerabilities(image)

        assert 'metadata' in vulnerabilities
        assert 'frequency' in vulnerabilities
        assert len(vulnerabilities) == 9

    def test_select_strategy(self):
        """Test strategy selection."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        vulnerabilities = self.cleaner._detect_vulnerabilities(image)
        strategy = self.cleaner._select_strategy(vulnerabilities)

        assert 'primary_attack' in strategy
        assert 'secondary_attack' in strategy
        assert 'weight' in strategy

    def test_apply_attack(self):
        """Test attack application."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        strategy = {
            'primary_attack': 'metadata_clean',
            'weight': {'metadata_clean': 0.5}
        }
        result = self.cleaner._apply_attack(image, strategy)

        assert result is not None
        assert result.shape == image.shape

    def test_update_weights(self):
        """Test weight updating."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        feedback = self.cleaner._get_feedback(image)
        initial_weights = self.cleaner.strategy_weights.copy()

        self.cleaner._update_weights(feedback)

        # Weights should be normalized
        total = sum(self.cleaner.strategy_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_pareto_front(self):
        """Test Pareto front management."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        feedback = self.cleaner._get_feedback(image)

        self.cleaner._update_pareto_front(image, feedback)
        assert len(self.cleaner.pareto_front) > 0

    def test_bayesian_optimizer(self):
        """Test Bayesian optimization."""
        assert self.cleaner.bayesian_optimizer is not None

        image = np.random.rand(64, 64, 3).astype(np.float32)
        feedback = self.cleaner._get_feedback(image)

        self.cleaner.bayesian_optimizer.update(image, feedback)
        params = self.cleaner.bayesian_optimizer.get_optimal_parameters()

        assert 'epsilon' in params
        assert 'steps' in params

    def test_get_feedback_history(self):
        """Test feedback history."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        feedback = self.cleaner._get_feedback(image)
        self.cleaner.feedback_history.append(list(feedback.values())[0])

        history = self.cleaner.get_feedback_history()
        assert len(history) > 0