"""
Semantic alias generator for creating human-readable, meaningful placeholders.
"""
import random
from typing import Dict, Set


class SemanticAliasGenerator:
    """Generates semantic aliases for entities like people, companies, and products."""

    def __init__(self):
        # Counter for sequential naming
        self._counters: Dict[str, int] = {}
        # Track used aliases to avoid duplicates
        self._used_aliases: Dict[str, Set[str]] = {}

        # Fake company names
        self.company_prefixes = [
            "Acme", "Global", "Tech", "Digital", "Smart", "Mega", "Prime",
            "Alpha", "Beta", "Omega", "Nexus", "Quantum", "Cyber", "Dynamic"
        ]
        self.company_suffixes = [
            "Corp", "Inc", "LLC", "Industries", "Solutions", "Systems",
            "Technologies", "Enterprises", "Group", "Partners", "Ventures"
        ]

        # Fake person first names
        self.first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily",
            "Robert", "Lisa", "James", "Maria", "William", "Patricia",
            "Richard", "Jennifer", "Thomas", "Linda", "Charles", "Susan"
        ]
        # Fake person last names
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
            "Miller", "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson",
            "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee"
        ]

        # Fake product names
        self.product_prefixes = [
            "Pro", "Ultra", "Super", "Mega", "Premium", "Elite",
            "Advanced", "Smart", "Turbo", "Power", "Max", "Plus"
        ]
        self.product_types = [
            "Suite", "Platform", "System", "Tool", "App", "Service",
            "Solution", "Engine", "Framework", "Hub", "Portal", "Cloud"
        ]

    def _get_counter(self, entity_type: str) -> int:
        """Get and increment counter for an entity type."""
        if entity_type not in self._counters:
            self._counters[entity_type] = 1
        else:
            self._counters[entity_type] += 1
        return self._counters[entity_type]

    def _ensure_unique(self, alias: str, entity_type: str) -> str:
        """Ensure the alias is unique by adding a suffix if needed."""
        if entity_type not in self._used_aliases:
            self._used_aliases[entity_type] = set()

        original_alias = alias
        counter = 1
        while alias in self._used_aliases[entity_type]:
            alias = f"{original_alias}_{counter}"
            counter += 1

        self._used_aliases[entity_type].add(alias)
        return alias

    def generate_company_name(self) -> str:
        """Generate a fake company name."""
        prefix = random.choice(self.company_prefixes)
        suffix = random.choice(self.company_suffixes)
        company_name = f"{prefix}_{suffix}"
        return self._ensure_unique(company_name.upper(), "COMPANY")

    def generate_person_name(self) -> str:
        """Generate a fake person name."""
        first = random.choice(self.first_names)
        last = random.choice(self.last_names)
        person_name = f"{first}_{last}"
        return self._ensure_unique(person_name.upper(), "PERSON")

    def generate_product_name(self) -> str:
        """Generate a fake product name."""
        prefix = random.choice(self.product_prefixes)
        product_type = random.choice(self.product_types)
        product_name = f"{prefix}{product_type}"
        return self._ensure_unique(product_name.upper(), "PRODUCT")

    def generate_location_name(self) -> str:
        """Generate a fake location name."""
        count = self._get_counter("LOCATION")
        return f"LOCATION_{count}"

    def generate_alias(self, entity_type: str, original_value: str = None) -> str:
        """
        Generate a semantic alias based on entity type.

        Args:
            entity_type: Type of entity (e.g., 'ORGANIZATION', 'PERSON', 'PRODUCT')
            original_value: The original value (optional, used for context)

        Returns:
            A semantic alias string
        """
        entity_type = entity_type.upper()

        # Map entity types to generator functions
        if entity_type in ['ORG', 'ORGANIZATION', 'COMPANY']:
            return self.generate_company_name()
        elif entity_type in ['PERSON', 'NAME', 'PER']:
            return self.generate_person_name()
        elif entity_type == 'PRODUCT':
            return self.generate_product_name()
        elif entity_type in ['GPE', 'LOCATION', 'LOC']:
            return self.generate_location_name()
        else:
            # For other types, use generic sequential naming
            count = self._get_counter(entity_type)
            alias = f"{entity_type}_{count}"
            return self._ensure_unique(alias, entity_type)

    def reset(self):
        """Reset all counters and tracking."""
        self._counters.clear()
        self._used_aliases.clear()
