"""
Synthetic Test Data Generator for PII Anonymizer Evaluation

Generates documents with known ground truth PII annotations for evaluation.
"""

import json
import os
import random
from typing import List, Dict
from datetime import datetime, timedelta


class SyntheticPIIGenerator:
    """Generates synthetic documents with known PII for testing"""

    def __init__(self, seed=42):
        random.seed(seed)

        # Test data pools
        self.emails = [
            "john.doe@example.com", "jane.smith@company.org", "bob.johnson@test.net",
            "alice.williams@email.com", "charlie.brown@domain.co", "david.miller@site.io",
            "emma.davis@provider.com", "frank.wilson@mail.net", "grace.lee@tech.org",
            "henry.taylor@business.com", "ivy.anderson@service.net", "jack.thomas@firm.com"
        ]

        self.phones = [
            "555-1234", "555-5678", "555-9012", "(555) 123-4567", "+1-555-987-6543",
            "555 234 5678", "(555)345-6789", "+1 555 456 7890", "555-567-8901",
            "(555) 678-9012", "555 789 0123", "+1-555-890-1234"
        ]

        self.ssns = [
            "123-45-6789", "987-65-4321", "555-12-3456", "111-22-3333",
            "999-88-7777", "444-55-6666", "222-33-4444", "888-99-0000",
            "777-88-9999", "333-44-5555", "666-77-8888", "000-11-2222"
        ]

        self.credit_cards = [
            "4532-1234-5678-9010", "5425 2334 4455 6677", "3782 822463 10005",
            "6011-1234-5678-9012", "4111111111111111", "5500000000000004",
            "3400 000000 00009", "6011000000000012", "4012888888881881",
            "5105105105105100", "3566002020360505", "6011111111111117"
        ]

        self.ip_addresses = [
            "192.168.1.1", "10.0.0.5", "172.16.0.100", "8.8.8.8",
            "192.168.0.254", "10.10.10.10", "172.31.255.255", "1.1.1.1",
            "192.168.100.1", "10.20.30.40", "172.16.50.60", "208.67.222.222"
        ]

        self.dates = [
            "01/15/1985", "12/31/2020", "06-15-1992", "03/22/2010",
            "09-10-1988", "11/05/2015", "07/04/1776", "02-14-2000",
            "10/31/1995", "04/01/2005", "08-25-1990", "05/17/2018"
        ]

        self.addresses = [
            "123 Main Street, Anytown, CA 90210",
            "456 Oak Avenue, Springfield, IL 62701",
            "789 Elm Road, Portland, OR 97201",
            "321 Pine Boulevard, Austin, TX 78701",
            "654 Maple Drive, Seattle, WA 98101",
            "987 Cedar Lane, Miami, FL 33101",
            "147 Birch Court, Denver, CO 80201",
            "258 Willow Way, Boston, MA 02101",
            "369 Spruce Street, Phoenix, AZ 85001",
            "741 Ash Avenue, Atlanta, GA 30301"
        ]

        self.urls = [
            "https://www.example.com", "http://test.org/page", "https://site.net/login",
            "http://www.domain.com/api", "https://service.io/dashboard", "http://platform.co/home",
            "https://portal.net/profile", "http://www.website.com/search", "https://app.org/settings",
            "http://system.com/admin"
        ]

        self.currency_amounts = [
            "$1,234.56", "$999,999.99", "€500.00", "£1,000.50",
            "$50.00", "€250.75", "£75.25", "$10,000.00",
            "¥5000", "$25,500.99", "€1,500.00", "£999.99"
        ]

        self.numbers = [
            "123456", "987654", "555123", "111222",
            "999888", "444555", "777666", "333444",
            "888999", "222111", "666777", "555000"
        ]

        self.person_names = [
            "John Doe", "Jane Smith", "Bob Johnson", "Alice Williams",
            "Charlie Brown", "David Miller", "Emma Davis", "Frank Wilson",
            "Grace Lee", "Henry Taylor", "Ivy Anderson", "Jack Thomas"
        ]

        self.organizations = [
            "Acme Corporation", "Global Industries Inc", "Tech Solutions LLC",
            "Digital Systems Corp", "Smart Enterprises", "Mega Technologies",
            "Prime Solutions Group", "Alpha Partners Ltd", "Beta Ventures Inc",
            "Omega Corporation", "Nexus Industries", "Quantum Systems"
        ]

        self.products = [
            "ProSuite X", "UltraPlatform 2000", "SuperSystem Pro", "MegaTool Plus",
            "PremiumApp Elite", "SmartService Cloud", "TurboEngine Advanced", "PowerHub Premium",
            "MaxPortal Ultra", "PlusFramework Pro", "EliteCloud Suite", "AdvancedPlatform X"
        ]

        self.locations = [
            "New York", "Los Angeles", "Chicago", "Houston",
            "Phoenix", "Philadelphia", "San Antonio", "San Diego",
            "Dallas", "San Jose", "Austin", "Jacksonville"
        ]

    def generate_text_document(self, doc_id: str, num_pii_instances=20) -> Dict:
        """Generate a text document with embedded PII"""
        pii_entities = []
        text_parts = []

        text_parts.append(f"Document ID: {doc_id}")
        text_parts.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        text_parts.append("\n")

        # Add emails
        for i in range(min(2, len(self.emails))):
            email = random.choice(self.emails)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Contact email: {email}")
            pii_entities.append({
                "text": email,
                "type": "EMAIL",
                "start": start_pos + 15,  # After "Contact email: "
                "end": start_pos + 15 + len(email)
            })

        # Add phones
        for i in range(min(2, len(self.phones))):
            phone = random.choice(self.phones)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Phone number: {phone}")
            pii_entities.append({
                "text": phone,
                "type": "PHONE",
                "start": start_pos + 14,
                "end": start_pos + 14 + len(phone)
            })

        # Add SSNs
        for i in range(min(2, len(self.ssns))):
            ssn = random.choice(self.ssns)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Social Security Number: {ssn}")
            pii_entities.append({
                "text": ssn,
                "type": "SSN",
                "start": start_pos + 24,
                "end": start_pos + 24 + len(ssn)
            })

        # Add credit cards
        for i in range(min(2, len(self.credit_cards))):
            cc = random.choice(self.credit_cards)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Credit card: {cc}")
            pii_entities.append({
                "text": cc,
                "type": "CREDIT_CARD",
                "start": start_pos + 13,
                "end": start_pos + 13 + len(cc)
            })

        # Add person names
        for i in range(min(2, len(self.person_names))):
            name = random.choice(self.person_names)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Employee: {name}")
            pii_entities.append({
                "text": name,
                "type": "PERSON",
                "start": start_pos + 10,
                "end": start_pos + 10 + len(name)
            })

        # Add organizations
        for i in range(min(2, len(self.organizations))):
            org = random.choice(self.organizations)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Company: {org}")
            pii_entities.append({
                "text": org,
                "type": "ORG",
                "start": start_pos + 9,
                "end": start_pos + 9 + len(org)
            })

        # Add products
        for i in range(min(1, len(self.products))):
            product = random.choice(self.products)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Using product: {product}")
            pii_entities.append({
                "text": product,
                "type": "PRODUCT",
                "start": start_pos + 15,
                "end": start_pos + 15 + len(product)
            })

        # Add locations
        for i in range(min(1, len(self.locations))):
            location = random.choice(self.locations)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Located in: {location}")
            pii_entities.append({
                "text": location,
                "type": "GPE",
                "start": start_pos + 12,
                "end": start_pos + 12 + len(location)
            })

        # Add IP addresses
        for i in range(min(1, len(self.ip_addresses))):
            ip = random.choice(self.ip_addresses)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Server IP: {ip}")
            pii_entities.append({
                "text": ip,
                "type": "IP_ADDRESS",
                "start": start_pos + 11,
                "end": start_pos + 11 + len(ip)
            })

        # Add dates
        for i in range(min(1, len(self.dates))):
            date = random.choice(self.dates)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Date of birth: {date}")
            pii_entities.append({
                "text": date,
                "type": "DATE",
                "start": start_pos + 15,
                "end": start_pos + 15 + len(date)
            })

        # Add addresses
        for i in range(min(1, len(self.addresses))):
            address = random.choice(self.addresses)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Address: {address}")
            pii_entities.append({
                "text": address,
                "type": "ADDRESS",
                "start": start_pos + 9,
                "end": start_pos + 9 + len(address)
            })

        # Add URLs
        for i in range(min(1, len(self.urls))):
            url = random.choice(self.urls)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Website: {url}")
            pii_entities.append({
                "text": url,
                "type": "URL",
                "start": start_pos + 9,
                "end": start_pos + 9 + len(url)
            })

        # Add currency
        for i in range(min(1, len(self.currency_amounts))):
            amount = random.choice(self.currency_amounts)
            start_pos = len("\n".join(text_parts))
            text_parts.append(f"Amount: {amount}")
            pii_entities.append({
                "text": amount,
                "type": "CURRENCY",
                "start": start_pos + 8,
                "end": start_pos + 8 + len(amount)
            })

        text = "\n".join(text_parts)

        return {
            "document_id": doc_id,
            "text": text,
            "pii_entities": pii_entities,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_pii_count": len(pii_entities)
            }
        }

    def generate_dataset(self, output_dir: str, num_documents=10):
        """Generate a dataset of synthetic documents with ground truth"""
        os.makedirs(output_dir, exist_ok=True)

        documents = []
        for i in range(num_documents):
            doc_id = f"synthetic_{i+1:03d}"
            doc = self.generate_text_document(doc_id)
            documents.append(doc)

            # Save individual document
            doc_path = os.path.join(output_dir, f"{doc_id}.txt")
            with open(doc_path, 'w') as f:
                f.write(doc["text"])

        # Save ground truth annotations
        ground_truth_path = os.path.join(output_dir, "ground_truth.json")
        with open(ground_truth_path, 'w') as f:
            json.dump(documents, f, indent=2)

        print(f"Generated {num_documents} synthetic documents in {output_dir}")
        print(f"Total PII instances: {sum(len(doc['pii_entities']) for doc in documents)}")
        print(f"Ground truth saved to: {ground_truth_path}")

        return documents


if __name__ == "__main__":
    generator = SyntheticPIIGenerator()
    output_dir = os.path.join(os.path.dirname(__file__), "synthetic")
    generator.generate_dataset(output_dir, num_documents=20)
