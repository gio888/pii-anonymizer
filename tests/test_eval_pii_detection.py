"""
Comprehensive Evaluation Test Suite for PII Detection

Tests PII detection accuracy against ground truth datasets.
Success Criteria:
- Detection rate >= 95%
- Zero PII leakage in anonymized output
"""

import unittest
import json
import os
import sys

# Add src and tests to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from pii_anonymizer.document_processor import PIIManager
from eval_framework import PIIGroundTruth, EvalRunner, EvalMetrics


class TestPIIDetectionEvaluation(unittest.TestCase):
    """Comprehensive evaluation of PII detection against ground truth"""

    @classmethod
    def setUpClass(cls):
        """Load ground truth datasets once for all tests"""
        # Initialize PII Manager with NER enabled
        cls.pii_manager = PIIManager(use_ner=True, use_semantic_aliases=True)

        # Load synthetic ground truth
        synthetic_path = os.path.join(
            os.path.dirname(__file__),
            'test_data',
            'synthetic',
            'ground_truth.json'
        )
        with open(synthetic_path, 'r') as f:
            cls.synthetic_data = json.load(f)

        # Load real-world ground truth
        realworld_path = os.path.join(
            os.path.dirname(__file__),
            'test_data',
            'realworld',
            'ground_truth.json'
        )
        with open(realworld_path, 'r') as f:
            cls.realworld_data = json.load(f)

        print(f"\n{'='*80}")
        print(f"Loaded {len(cls.synthetic_data)} synthetic documents")
        print(f"Loaded {len(cls.realworld_data)} real-world documents")
        print(f"{'='*80}\n")

    def setUp(self):
        """Set up fresh eval runner for each test"""
        self.eval_runner = EvalRunner(self.pii_manager)

    def test_synthetic_dataset_full_eval(self):
        """Evaluate PII detection on synthetic dataset"""
        print("\n" + "="*80)
        print("EVALUATING SYNTHETIC DATASET")
        print("="*80 + "\n")

        for doc_data in self.synthetic_data:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            # Evaluate document
            detection_result, leakage_result = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

            # Print progress
            detected_count = sum(len(v) for v in detection_result.detected_pii.values())
            missed_count = sum(len(v) for v in detection_result.missed_pii.values())
            print(f"{doc_data['document_id']}: "
                  f"Detected {detected_count}, "
                  f"Missed {missed_count}, "
                  f"Leaked {leakage_result.leakage_count}")

        # Get metrics
        metrics = self.eval_runner.get_metrics()

        # Print report
        print("\n" + metrics.generate_report())

        # Save results
        results_dir = os.path.join(os.path.dirname(__file__), 'eval_results')
        os.makedirs(results_dir, exist_ok=True)
        self.eval_runner.save_results(os.path.join(results_dir, 'synthetic_results.json'))

        # Check success criteria
        success, failures = metrics.check_success_criteria()
        if not success:
            self.fail(f"Synthetic eval failed: {'; '.join(failures)}")

    def test_realworld_dataset_full_eval(self):
        """Evaluate PII detection on real-world dataset"""
        print("\n" + "="*80)
        print("EVALUATING REAL-WORLD DATASET")
        print("="*80 + "\n")

        for doc_data in self.realworld_data:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            # Evaluate document
            detection_result, leakage_result = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

            # Print progress
            detected_count = sum(len(v) for v in detection_result.detected_pii.values())
            missed_count = sum(len(v) for v in detection_result.missed_pii.values())
            print(f"{doc_data['document_id']}: "
                  f"Detected {detected_count}, "
                  f"Missed {missed_count}, "
                  f"Leaked {leakage_result.leakage_count}")

        # Get metrics
        metrics = self.eval_runner.get_metrics()

        # Print report
        print("\n" + metrics.generate_report())

        # Save results
        results_dir = os.path.join(os.path.dirname(__file__), 'eval_results')
        os.makedirs(results_dir, exist_ok=True)
        self.eval_runner.save_results(os.path.join(results_dir, 'realworld_results.json'))

        # Check success criteria
        success, failures = metrics.check_success_criteria()
        if not success:
            self.fail(f"Real-world eval failed: {'; '.join(failures)}")

    def test_email_detection(self):
        """Test EMAIL detection specifically"""
        print("\n" + "="*80)
        print("TESTING EMAIL DETECTION")
        print("="*80 + "\n")

        # Filter for documents with EMAIL entities
        email_docs = [
            doc for doc in self.synthetic_data + self.realworld_data
            if any(entity["type"] == "EMAIL" for entity in doc["pii_entities"])
        ]

        for doc_data in email_docs:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            detection_result, _ = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

        # Get EMAIL-specific metrics
        metrics = self.eval_runner.get_metrics()
        if "EMAIL" in metrics.metrics_by_type:
            email_metrics = metrics.get_type_metrics("EMAIL")
            print(f"EMAIL Detection Rate: {email_metrics['recall']:.2%}")
            print(f"EMAIL Precision: {email_metrics['precision']:.2%}")
            print(f"EMAIL F1: {email_metrics['f1']:.2%}")

            self.assertGreaterEqual(email_metrics['recall'], 0.95,
                                  f"EMAIL detection rate {email_metrics['recall']:.2%} < 95%")

    def test_phone_detection(self):
        """Test PHONE detection specifically"""
        print("\n" + "="*80)
        print("TESTING PHONE DETECTION")
        print("="*80 + "\n")

        phone_docs = [
            doc for doc in self.synthetic_data + self.realworld_data
            if any(entity["type"] == "PHONE" for entity in doc["pii_entities"])
        ]

        for doc_data in phone_docs:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            detection_result, _ = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

        metrics = self.eval_runner.get_metrics()
        if "PHONE" in metrics.metrics_by_type:
            phone_metrics = metrics.get_type_metrics("PHONE")
            print(f"PHONE Detection Rate: {phone_metrics['recall']:.2%}")
            print(f"PHONE Precision: {phone_metrics['precision']:.2%}")
            print(f"PHONE F1: {phone_metrics['f1']:.2%}")

            self.assertGreaterEqual(phone_metrics['recall'], 0.95,
                                  f"PHONE detection rate {phone_metrics['recall']:.2%} < 95%")

    def test_person_detection_ner(self):
        """Test PERSON detection via spaCy NER"""
        print("\n" + "="*80)
        print("TESTING PERSON DETECTION (NER)")
        print("="*80 + "\n")

        person_docs = [
            doc for doc in self.synthetic_data + self.realworld_data
            if any(entity["type"] == "PERSON" for entity in doc["pii_entities"])
        ]

        for doc_data in person_docs:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            detection_result, _ = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

        metrics = self.eval_runner.get_metrics()
        if "PERSON" in metrics.metrics_by_type:
            person_metrics = metrics.get_type_metrics("PERSON")
            print(f"PERSON Detection Rate: {person_metrics['recall']:.2%}")
            print(f"PERSON Precision: {person_metrics['precision']:.2%}")
            print(f"PERSON F1: {person_metrics['f1']:.2%}")

            self.assertGreaterEqual(person_metrics['recall'], 0.95,
                                  f"PERSON detection rate {person_metrics['recall']:.2%} < 95%")

    def test_organization_detection_ner(self):
        """Test ORG detection via spaCy NER"""
        print("\n" + "="*80)
        print("TESTING ORGANIZATION DETECTION (NER)")
        print("="*80 + "\n")

        org_docs = [
            doc for doc in self.synthetic_data + self.realworld_data
            if any(entity["type"] == "ORG" for entity in doc["pii_entities"])
        ]

        for doc_data in org_docs:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            detection_result, _ = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

        metrics = self.eval_runner.get_metrics()
        if "ORG" in metrics.metrics_by_type:
            org_metrics = metrics.get_type_metrics("ORG")
            print(f"ORG Detection Rate: {org_metrics['recall']:.2%}")
            print(f"ORG Precision: {org_metrics['precision']:.2%}")
            print(f"ORG F1: {org_metrics['f1']:.2%}")

            self.assertGreaterEqual(org_metrics['recall'], 0.95,
                                  f"ORG detection rate {org_metrics['recall']:.2%} < 95%")

    def test_zero_leakage(self):
        """Test that no PII leaks into anonymized documents"""
        print("\n" + "="*80)
        print("TESTING ZERO PII LEAKAGE")
        print("="*80 + "\n")

        all_docs = self.synthetic_data + self.realworld_data

        for doc_data in all_docs:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            _, leakage_result = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

            if leakage_result.has_leakage:
                print(f"❌ LEAKAGE in {doc_data['document_id']}: {leakage_result.leaked_pii}")

        metrics = self.eval_runner.get_metrics()
        leakage_rate = metrics.calculate_leakage_rate()

        print(f"\nTotal Leaked PII: {metrics.total_leaked_pii}")
        print(f"Leakage Rate: {leakage_rate:.2%}")

        self.assertEqual(metrics.total_leaked_pii, 0,
                        f"PII leakage detected: {metrics.total_leaked_pii} instances")

    def test_combined_dataset_success_criteria(self):
        """Test combined synthetic + real-world dataset against success criteria"""
        print("\n" + "="*80)
        print("COMBINED DATASET EVALUATION")
        print("="*80 + "\n")

        all_docs = self.synthetic_data + self.realworld_data

        for doc_data in all_docs:
            ground_truth = PIIGroundTruth(
                document_id=doc_data["document_id"],
                file_path="",
                pii_entities=doc_data["pii_entities"]
            )

            detection_result, leakage_result = self.eval_runner.evaluate_document(
                doc_data["text"],
                ground_truth
            )

        # Get final metrics
        metrics = self.eval_runner.get_metrics()

        # Print comprehensive report
        print("\n" + metrics.generate_report())

        # Save combined results
        results_dir = os.path.join(os.path.dirname(__file__), 'eval_results')
        os.makedirs(results_dir, exist_ok=True)
        self.eval_runner.save_results(os.path.join(results_dir, 'combined_results.json'))

        # Check success criteria
        success, failures = metrics.check_success_criteria()

        # Assert criteria met
        self.assertTrue(success, f"Success criteria not met: {'; '.join(failures)}")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
