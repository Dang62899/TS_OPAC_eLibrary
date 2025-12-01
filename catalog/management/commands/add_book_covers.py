from django.core.management.base import BaseCommand
from catalog.models import Publication


class Command(BaseCommand):
    help = 'Assign sample book cover images to publications without covers'

    def handle(self, *args, **options):
        # Book IDs without covers and their corresponding SVG cover numbers
        book_covers_mapping = {
            27: 'books/sample_7.svg',   # Access Control Implementation Manual
            37: 'books/sample_8.svg',   # Capstone: Advanced Threat Detection System
            38: 'books/sample_9.svg',   # Capstone: Zero Trust Architecture Implementation
            33: 'books/sample_10.svg',  # Cloud Security Assessment Procedures
            35: 'books/sample_11.svg',  # Compliance Audit Procedures
            23: 'books/sample_12.svg',  # Cybersecurity Operations SOP
            24: 'books/sample_13.svg',  # Data Classification Standard
            30: 'books/sample_14.svg',  # Forensics and Evidence Handling SOP
            22: 'books/sample_15.svg',  # Incident Response Procedures Guide
            28: 'books/sample_16.svg',  # Malware Analysis Procedures
            29: 'books/sample_17.svg',  # Network Architecture Design Guide
            21: 'books/sample_18.svg',  # Network Security Fundamentals Manual
            31: 'books/sample_19.svg',  # Penetration Testing Framework
            32: 'books/sample_20.svg',  # SIEM Administration Manual
            34: 'books/sample_21.svg',  # Intrusion Detection System Tuning Guide
            36: 'books/sample_25.svg',  # Security Awareness Training Materials
            40: 'books/sample_26.svg',  # Security Patch Management SOP
            26: 'books/sample_27.svg',  # Threat Intelligence Analysis TTP
            25: 'books/sample_28.svg',  # Vulnerability Management Process
            39: 'books/sample_29.svg',  # Wireless Security Assessment TTP
        }

        updated_count = 0
        for book_id, cover_path in book_covers_mapping.items():
            try:
                publication = Publication.objects.get(id=book_id)
                publication.cover_image = cover_path
                publication.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Updated: {publication.title}'
                    )
                )
            except Publication.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Publication with ID {book_id} not found'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully updated {updated_count} publications with cover images!'
            )
        )
