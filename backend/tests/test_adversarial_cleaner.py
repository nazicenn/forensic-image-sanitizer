import pytest
import numpy as np
from app.services.forensic_cleaner import AdversarialCleaner


class TestAdversarialCleaner:
    """Test AdversarialCleaner class."""

    def setup_method(self):
        self.cleaner = AdversarialCleaner()

    def test_cleaner_init(self):
        """Test AdversarialCleaner initialization."""
        assert self.cleaner is not None
        assert self.cleaner.epsilon == 0.03
        assert self.cleaner.steps == 10

    def test_fgsm_attack(self):
        """Test FGSM attack."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        result = self.cleaner._fgsm_attack(image, 0.03)

        assert result is not None
        assert result.shape == image.shape
        assert np.all(result >= 0) and np.all(result <= 1)

    def test_pgd_attack(self):
        """Test PGD attack."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        result = self.cleaner._pgd_attack(image, 0.03)

        assert result is not None
        assert result.shape == image.shape
        assert np.all(result >= 0) and np.all(result <= 1)

    def test_ensemble_attack(self):
        """Test ensemble attack."""
        image = np.random.rand(64, 64, 3).astype(np.float32)
        result = self.cleaner._ensemble_attack(image, 0.03)

        assert result is not None
        assert result.shape == image.shape
        assert np.all(result >= 0) and np.all(result <= 1)

    def test_clean_all(self):
        """Test clean_all with adversarial perturbations."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.cleaner.clean_all(image, attack_type='ensemble')

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_detect_adversarial(self):
        """Test adversarial detection."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.cleaner.detect_adversarial(image)

        assert 'has_adversarial' in result
        assert 'metrics' in result
        assert 'confidence' in result

    def test_adaptive_perturbation(self):
        """Test adaptive perturbation."""
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = self.cleaner.adaptive_perturbation(image, 0.03)

        assert result is not None
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_freq_domain_attack(self):
        """Test frequency domain attack."""
        image = np.random.rand(64, 64).astype(np.float32)
        result = self.cleaner._freq_domain_attack(image, 0.03)

        assert result is not None
        assert result.shape == image.shape
        assert np.all(result >= 0) and np.all(result <= 1)

    def test_spatial_domain_attack(self):
        """Test spatial domain attack."""
        image = np.random.rand(64, 64).astype(np.float32)
        result = self.cleaner._spatial_domain_attack(image, 0.03)

        assert result is not None
        assert result.shape == image.shape
        assert np.all(result >= 0) and np.all(result <= 1)