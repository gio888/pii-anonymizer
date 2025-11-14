"""
Evaluation Framework for PII Anonymizer

Provides metrics tracking, evaluation runners, and reporting for PII detection quality.
Success criteria:
- PII detection rate >= 95%
- Zero PII leakage in anonymized output
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import re


@dataclass
class PIIGroundTruth:
    """Ground truth PII annotations for a document"""
    document_id: str
    file_path: str
    pii_entities: List[Dict[str, str]]  # [{"text": "john@example.com", "type": "EMAIL", "start": 10, "end": 27}, ...]

    def get_pii_by_type(self, pii_type: str) -> List[str]:
        """Get all PII texts of a specific type"""
        return [entity["text"] for entity in self.pii_entities if entity["type"] == pii_type]

    def get_all_pii_texts(self) -> Set[str]:
        """Get all PII texts regardless of type"""
        return {entity["text"] for entity in self.pii_entities}


@dataclass
class DetectionResult:
    """Result of PII detection on a single document"""
    document_id: str
    detected_pii: Dict[str, List[str]]  # {"EMAIL": ["john@example.com"], "PHONE": ["555-1234"]}
    missed_pii: Dict[str, List[str]]  # Ground truth PII that was not detected
    false_positives: Dict[str, List[str]]  # Detected items not in ground truth

    def get_all_detected(self) -> Set[str]:
        """Get all detected PII texts"""
        result = set()
        for pii_list in self.detected_pii.values():
            result.update(pii_list)
        return result


@dataclass
class LeakageResult:
    """Result of PII leakage check in anonymized document"""
    document_id: str
    leaked_pii: List[str]  # Original PII found in anonymized text
    has_leakage: bool
    leakage_count: int


@dataclass
class EvalMetrics:
    """Evaluation metrics for PII detection"""
    # Per-document results
    detection_results: List[DetectionResult] = field(default_factory=list)
    leakage_results: List[LeakageResult] = field(default_factory=list)

    # Aggregated metrics
    total_ground_truth_pii: int = 0
    total_detected_pii: int = 0
    total_true_positives: int = 0
    total_false_positives: int = 0
    total_false_negatives: int = 0
    total_leaked_pii: int = 0

    # Per-type metrics
    metrics_by_type: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {
        "ground_truth": 0,
        "detected": 0,
        "true_positives": 0,
        "false_positives": 0,
        "false_negatives": 0
    }))

    def add_detection_result(self, result: DetectionResult):
        """Add a detection result and update metrics"""
        self.detection_results.append(result)

        # Update per-type metrics
        for pii_type, detected_list in result.detected_pii.items():
            for pii_text in detected_list:
                self.metrics_by_type[pii_type]["detected"] += 1
                # Check if it's a true positive
                if pii_type in result.missed_pii:
                    # Not in missed, so it's detected
                    self.metrics_by_type[pii_type]["true_positives"] += 1
                    self.total_true_positives += 1

        for pii_type, missed_list in result.missed_pii.items():
            self.metrics_by_type[pii_type]["ground_truth"] += len(missed_list)
            self.metrics_by_type[pii_type]["false_negatives"] += len(missed_list)
            self.total_ground_truth_pii += len(missed_list)
            self.total_false_negatives += len(missed_list)

        for pii_type, fp_list in result.false_positives.items():
            self.metrics_by_type[pii_type]["false_positives"] += len(fp_list)
            self.total_false_positives += len(fp_list)

    def add_leakage_result(self, result: LeakageResult):
        """Add a leakage result and update metrics"""
        self.leakage_results.append(result)
        self.total_leaked_pii += result.leakage_count

    def calculate_precision(self) -> float:
        """Calculate overall precision (TP / (TP + FP))"""
        denominator = self.total_true_positives + self.total_false_positives
        if denominator == 0:
            return 0.0
        return self.total_true_positives / denominator

    def calculate_recall(self) -> float:
        """Calculate overall recall (TP / (TP + FN))"""
        denominator = self.total_true_positives + self.total_false_negatives
        if denominator == 0:
            return 0.0
        return self.total_true_positives / denominator

    def calculate_f1(self) -> float:
        """Calculate overall F1 score"""
        precision = self.calculate_precision()
        recall = self.calculate_recall()
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def calculate_detection_rate(self) -> float:
        """Calculate detection rate (same as recall)"""
        return self.calculate_recall()

    def calculate_leakage_rate(self) -> float:
        """Calculate leakage rate (leaked / total ground truth)"""
        if self.total_ground_truth_pii == 0:
            return 0.0
        return self.total_leaked_pii / self.total_ground_truth_pii

    def get_type_metrics(self, pii_type: str) -> Dict[str, float]:
        """Calculate precision, recall, F1 for a specific PII type"""
        metrics = self.metrics_by_type[pii_type]
        tp = metrics["true_positives"]
        fp = metrics["false_positives"]
        fn = metrics["false_negatives"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "ground_truth": metrics["ground_truth"],
            "detected": metrics["detected"]
        }

    def check_success_criteria(self) -> Tuple[bool, List[str]]:
        """
        Check if success criteria are met:
        - Detection rate >= 95%
        - Zero PII leakage

        Returns: (success: bool, failure_reasons: List[str])
        """
        failures = []

        detection_rate = self.calculate_detection_rate()
        if detection_rate < 0.95:
            failures.append(f"Detection rate {detection_rate:.2%} < 95%")

        leakage_rate = self.calculate_leakage_rate()
        if leakage_rate > 0:
            failures.append(f"PII leakage detected: {self.total_leaked_pii} instances ({leakage_rate:.2%})")

        return (len(failures) == 0, failures)

    def generate_report(self) -> str:
        """Generate a detailed evaluation report"""
        success, failures = self.check_success_criteria()

        report = []
        report.append("=" * 80)
        report.append("PII ANONYMIZER EVALUATION REPORT")
        report.append("=" * 80)
        report.append("")

        # Overall status
        if success:
            report.append("✅ SUCCESS: All criteria met!")
        else:
            report.append("❌ FAILURE: Criteria not met")
            for failure in failures:
                report.append(f"   - {failure}")
        report.append("")

        # Overall metrics
        report.append("OVERALL METRICS")
        report.append("-" * 80)
        report.append(f"Detection Rate (Recall): {self.calculate_detection_rate():.2%} (target: ≥95%)")
        report.append(f"Precision:               {self.calculate_precision():.2%}")
        report.append(f"F1 Score:                {self.calculate_f1():.2%}")
        report.append(f"Leakage Rate:            {self.calculate_leakage_rate():.2%} (target: 0%)")
        report.append("")
        report.append(f"Ground Truth PII:        {self.total_ground_truth_pii}")
        report.append(f"True Positives:          {self.total_true_positives}")
        report.append(f"False Positives:         {self.total_false_positives}")
        report.append(f"False Negatives:         {self.total_false_negatives}")
        report.append(f"Leaked PII Instances:    {self.total_leaked_pii}")
        report.append("")

        # Per-type breakdown
        report.append("PER-TYPE METRICS")
        report.append("-" * 80)
        report.append(f"{'Type':<20} {'Precision':<12} {'Recall':<12} {'F1':<12} {'TP':<8} {'FP':<8} {'FN':<8}")
        report.append("-" * 80)

        for pii_type in sorted(self.metrics_by_type.keys()):
            type_metrics = self.get_type_metrics(pii_type)
            report.append(
                f"{pii_type:<20} "
                f"{type_metrics['precision']:<12.2%} "
                f"{type_metrics['recall']:<12.2%} "
                f"{type_metrics['f1']:<12.2%} "
                f"{type_metrics['true_positives']:<8} "
                f"{type_metrics['false_positives']:<8} "
                f"{type_metrics['false_negatives']:<8}"
            )
        report.append("")

        # Leakage details
        if self.total_leaked_pii > 0:
            report.append("LEAKAGE DETAILS")
            report.append("-" * 80)
            for leakage in self.leakage_results:
                if leakage.has_leakage:
                    report.append(f"Document: {leakage.document_id}")
                    report.append(f"  Leaked PII: {', '.join(leakage.leaked_pii[:10])}")
                    if len(leakage.leaked_pii) > 10:
                        report.append(f"  ... and {len(leakage.leaked_pii) - 10} more")
            report.append("")

        # Documents tested
        report.append("DOCUMENTS TESTED")
        report.append("-" * 80)
        report.append(f"Total documents: {len(self.detection_results)}")
        report.append(f"Documents with leakage: {sum(1 for r in self.leakage_results if r.has_leakage)}")
        report.append("")

        return "\n".join(report)


class EvalRunner:
    """Runs PII detection evaluations and collects metrics"""

    def __init__(self, pii_manager):
        """
        Initialize eval runner

        Args:
            pii_manager: Instance of PIIManager to evaluate
        """
        self.pii_manager = pii_manager
        self.metrics = EvalMetrics()

        # Type normalization mapping (to handle NAME/PERSON, LOCATION/GPE, ORGANIZATION/ORG)
        self.type_normalization = {
            'PERSON': 'NAME',
            'GPE': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'LOC': 'LOCATION',
            'PER': 'NAME'
        }

    def normalize_type(self, pii_type: str) -> str:
        """Normalize PII type for comparison"""
        return self.type_normalization.get(pii_type, pii_type)

    def evaluate_detection(self, text: str, ground_truth: PIIGroundTruth) -> DetectionResult:
        """
        Evaluate PII detection on a single document

        Args:
            text: Document text
            ground_truth: Ground truth PII annotations

        Returns:
            DetectionResult with detected, missed, and false positive PII
        """
        # Detect PII using the system
        detections = self.pii_manager.detect_pii_in_text(text)

        # Organize detections by type (normalized)
        detected_by_type = defaultdict(list)
        for original, pii_type, placeholder in detections:
            normalized_type = self.normalize_type(pii_type)
            detected_by_type[normalized_type].append(original)

        # Compare with ground truth (normalized)
        ground_truth_by_type = defaultdict(list)
        for entity in ground_truth.pii_entities:
            normalized_type = self.normalize_type(entity["type"])
            ground_truth_by_type[normalized_type].append(entity["text"])

        # Calculate missed and false positives
        missed_by_type = {}
        false_positives_by_type = {}

        all_types = set(ground_truth_by_type.keys()) | set(detected_by_type.keys())

        for pii_type in all_types:
            gt_set = set(ground_truth_by_type.get(pii_type, []))
            det_set = set(detected_by_type.get(pii_type, []))

            missed = gt_set - det_set
            false_pos = det_set - gt_set

            if missed:
                missed_by_type[pii_type] = list(missed)
            if false_pos:
                false_positives_by_type[pii_type] = list(false_pos)

        result = DetectionResult(
            document_id=ground_truth.document_id,
            detected_pii=dict(detected_by_type),
            missed_pii=missed_by_type,
            false_positives=false_positives_by_type
        )

        self.metrics.add_detection_result(result)
        return result

    def evaluate_leakage(self, anonymized_text: str, ground_truth: PIIGroundTruth) -> LeakageResult:
        """
        Check if any original PII leaked into anonymized text

        Args:
            anonymized_text: Anonymized document text
            ground_truth: Ground truth PII annotations

        Returns:
            LeakageResult indicating any leaked PII
        """
        leaked = []
        ground_truth_pii = ground_truth.get_all_pii_texts()

        for pii_text in ground_truth_pii:
            # Check if original PII appears in anonymized text
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(pii_text) + r'\b'
            if re.search(pattern, anonymized_text, re.IGNORECASE):
                leaked.append(pii_text)

        result = LeakageResult(
            document_id=ground_truth.document_id,
            leaked_pii=leaked,
            has_leakage=len(leaked) > 0,
            leakage_count=len(leaked)
        )

        self.metrics.add_leakage_result(result)
        return result

    def evaluate_document(self, text: str, ground_truth: PIIGroundTruth) -> Tuple[DetectionResult, LeakageResult]:
        """
        Evaluate both detection and leakage for a document

        Args:
            text: Original document text
            ground_truth: Ground truth PII annotations

        Returns:
            Tuple of (DetectionResult, LeakageResult)
        """
        # Evaluate detection
        detection_result = self.evaluate_detection(text, ground_truth)

        # Anonymize the text
        anonymized_text = self.pii_manager.anonymize_text(text)

        # Evaluate leakage
        leakage_result = self.evaluate_leakage(anonymized_text, ground_truth)

        return detection_result, leakage_result

    def get_metrics(self) -> EvalMetrics:
        """Get the current evaluation metrics"""
        return self.metrics

    def reset_metrics(self):
        """Reset metrics for a new evaluation run"""
        self.metrics = EvalMetrics()

    def save_results(self, output_path: str):
        """Save evaluation results to JSON file"""
        results = {
            "overall_metrics": {
                "detection_rate": self.metrics.calculate_detection_rate(),
                "precision": self.metrics.calculate_precision(),
                "recall": self.metrics.calculate_recall(),
                "f1_score": self.metrics.calculate_f1(),
                "leakage_rate": self.metrics.calculate_leakage_rate(),
                "total_ground_truth_pii": self.metrics.total_ground_truth_pii,
                "total_true_positives": self.metrics.total_true_positives,
                "total_false_positives": self.metrics.total_false_positives,
                "total_false_negatives": self.metrics.total_false_negatives,
                "total_leaked_pii": self.metrics.total_leaked_pii
            },
            "per_type_metrics": {
                pii_type: self.metrics.get_type_metrics(pii_type)
                for pii_type in self.metrics.metrics_by_type.keys()
            },
            "success_criteria": {
                "passed": self.metrics.check_success_criteria()[0],
                "failures": self.metrics.check_success_criteria()[1]
            },
            "detection_results": [
                {
                    "document_id": r.document_id,
                    "detected_pii": r.detected_pii,
                    "missed_pii": r.missed_pii,
                    "false_positives": r.false_positives
                }
                for r in self.metrics.detection_results
            ],
            "leakage_results": [
                {
                    "document_id": r.document_id,
                    "has_leakage": r.has_leakage,
                    "leaked_pii": r.leaked_pii,
                    "leakage_count": r.leakage_count
                }
                for r in self.metrics.leakage_results
            ]
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
