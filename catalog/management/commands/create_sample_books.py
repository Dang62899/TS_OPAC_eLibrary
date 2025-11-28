"""
Management command to create sample publications for demonstration
"""
from django.core.management.base import BaseCommand
from datetime import datetime
import random

from catalog.models import PublicationType, Subject, Author, Publisher, Location, Publication, Item
    PublicationType, Subject, Author, Publisher,
    Location, Publication, Item
)

class Command(BaseCommand):
    help = 'Creates sample publications for demonstration purposes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        # Create sample data for each publication type
        self.create_manuals()
        self.create_sops()
        self.create_capstone_projects()
        self.create_ttps()

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))

    def create_manuals(self):
        """Create sample Manuals"""
        pub_type, _ = PublicationType.objects.get_or_create(
            code='MAN',
            defaults={'name': 'Manual', 'description': 'Technical and operational manuals'}
        )

        publisher, _ = Publisher.objects.get_or_create(
            name='Technical Publications Inc.',
            defaults={'website': 'https://techpub.example.com'}
        )

        location, _ = Location.objects.get_or_create(
            code='MAIN',
            defaults={'name': 'Main Library', 'description': 'Main collection', 'is_physical': True}
        )

        subjects_list = [
            'Computer Systems', 'Network Administration', 'Database Management',
            'Software Engineering', 'System Security', 'IT Operations'
        ]

        subjects = []
        for subject_name in subjects_list:
            subject, _ = Subject.objects.get_or_create(name=subject_name)
            subjects.append(subject)

        manuals = [
            {
                'title': 'Advanced Network Configuration Guide',
                'subtitle': 'Comprehensive Network Setup and Management',
                'abstract': 'Complete guide to configuring and managing enterprise networks, including routers, switches, and firewalls.',
                'isbn': '978-1-234-56780-1',
                'call_number': 'MAN.004.6',
                'pages': 450,
            },
            {
                'title': 'Database Administration Handbook',
                'subtitle': 'Best Practices for Database Management',
                'abstract': 'Essential handbook covering database design, optimization, backup, and recovery procedures.',
                'isbn': '978-1-234-56781-8',
                'call_number': 'MAN.005.74',
                'pages': 520,
            },
            {
                'title': 'System Security Operations Manual',
                'subtitle': 'Protecting Information Assets',
                'abstract': 'Comprehensive manual on implementing and maintaining security measures in IT systems.',
                'isbn': '978-1-234-56782-5',
                'call_number': 'MAN.005.8',
                'pages': 380,
            },
            {
                'title': 'Cloud Infrastructure Management',
                'subtitle': 'AWS, Azure, and GCP Administration',
                'abstract': 'Complete guide to managing cloud infrastructure across major platforms.',
                'isbn': '978-1-234-56783-2',
                'call_number': 'MAN.004.678',
                'pages': 600,
            },
            {
                'title': 'DevOps Practices Manual',
                'subtitle': 'Continuous Integration and Deployment',
                'abstract': 'Practical guide to implementing DevOps methodologies and tools.',
                'isbn': '978-1-234-56784-9',
                'call_number': 'MAN.005.1',
                'pages': 420,
            },
            {
                'title': 'Linux System Administration Guide',
                'subtitle': 'Enterprise Linux Management',
                'abstract': 'Comprehensive manual for administering Linux systems in enterprise environments.',
                'isbn': '978-1-234-56785-6',
                'call_number': 'MAN.005.43',
                'pages': 550,
            },
            {
                'title': 'Virtualization Technology Handbook',
                'subtitle': 'VMware and Hyper-V Administration',
                'abstract': 'Complete guide to virtual machine deployment and management.',
                'isbn': '978-1-234-56786-3',
                'call_number': 'MAN.005.4476',
                'pages': 480,
            },
            {
                'title': 'Cybersecurity Incident Response Manual',
                'subtitle': 'Handling Security Breaches',
                'abstract': 'Step-by-step procedures for responding to cybersecurity incidents.',
                'isbn': '978-1-234-56787-0',
                'call_number': 'MAN.005.84',
                'pages': 350,
            },
            {
                'title': 'IT Service Management Guide',
                'subtitle': 'ITIL Framework Implementation',
                'abstract': 'Practical guide to implementing ITIL best practices.',
                'isbn': '978-1-234-56788-7',
                'call_number': 'MAN.004.068',
                'pages': 400,
            },
            {
                'title': 'Enterprise Backup and Recovery',
                'subtitle': 'Data Protection Strategies',
                'abstract': 'Comprehensive manual on backup solutions and disaster recovery planning.',
                'isbn': '978-1-234-56789-4',
                'call_number': 'MAN.005.74',
                'pages': 390,
            },
        ]

        for idx, manual_data in enumerate(manuals, 1):
            # Create authors
            author1, _ = Author.objects.get_or_create(
                first_name=f'John',
                last_name=f'Tech{idx}',
                defaults={'bio': 'Experienced IT professional and technical writer'}
            )
            author2, _ = Author.objects.get_or_create(
                first_name=f'Jane',
                last_name=f'Expert{idx}',
                defaults={'bio': 'Senior systems engineer and consultant'}
            )

            # Create publication
            pub, created = Publication.objects.get_or_create(
                isbn=manual_data['isbn'],
                defaults={
                    'title': manual_data['title'],
                    'subtitle': manual_data['subtitle'],
                    'publication_type': pub_type,
                    'publisher': publisher,
                    'publication_date': datetime(2020 + idx % 5, (idx % 12) + 1, 1).date(),
                    'edition': f'{idx}st Edition' if idx == 1 else f'{idx}nd Edition' if idx == 2 else f'{idx}rd Edition' if idx == 3 else f'{idx}th Edition',
                    'language': 'English',
                    'pages': manual_data['pages'],
                    'call_number': manual_data['call_number'],
                    'abstract': manual_data['abstract'],
                }
            )

            if created:
                pub.authors.add(author1, author2)
                pub.subjects.add(*random.sample(subjects, 3))

                # Create 2-3 items per publication
                for i in range(random.randint(2, 3)):
                    Item.objects.create(
                        publication=pub,
                        barcode=f'MAN{idx:03d}{i+1:02d}',
                        location=location,
                        status='available',
                        condition='good'
                    )

        self.stdout.write(self.style.SUCCESS(f'Created {len(manuals)} Manuals'))

    def create_sops(self):
        """Create sample SOPs (Standard Operating Procedures)"""
        pub_type, _ = PublicationType.objects.get_or_create(
            code='SOP',
            defaults={'name': 'SOP', 'description': 'Standard Operating Procedures'}
        )

        publisher, _ = Publisher.objects.get_or_create(
            name='Standards & Procedures Publishing',
            defaults={'website': 'https://soppub.example.com'}
        )

        location, _ = Location.objects.get_or_create(
            code='REF',
            defaults={'name': 'Reference Section', 'description': 'Reference materials', 'is_physical': True}
        )

        subjects_list = [
            'Quality Assurance', 'Safety Procedures', 'Compliance',
            'Operations Management', 'Process Documentation'
        ]

        subjects = []
        for subject_name in subjects_list:
            subject, _ = Subject.objects.get_or_create(name=subject_name)
            subjects.append(subject)

        sops = [
            {
                'title': 'Software Testing Standard Operating Procedure',
                'abstract': 'Standardized procedures for software quality assurance and testing.',
                'call_number': 'SOP.005.14',
                'pages': 150,
            },
            {
                'title': 'Data Center Operations SOP',
                'abstract': 'Standard procedures for managing data center facilities and equipment.',
                'call_number': 'SOP.004.6',
                'pages': 200,
            },
            {
                'title': 'Change Management Procedures',
                'abstract': 'Formal procedures for managing IT system changes.',
                'call_number': 'SOP.004.068',
                'pages': 120,
            },
            {
                'title': 'Security Audit Procedures',
                'abstract': 'Step-by-step procedures for conducting security audits.',
                'call_number': 'SOP.005.8',
                'pages': 180,
            },
            {
                'title': 'Network Maintenance SOP',
                'abstract': 'Standard procedures for routine network maintenance.',
                'call_number': 'SOP.004.6',
                'pages': 160,
            },
            {
                'title': 'Incident Reporting Procedures',
                'abstract': 'Standardized procedures for reporting and documenting IT incidents.',
                'call_number': 'SOP.004.068',
                'pages': 100,
            },
            {
                'title': 'User Account Management SOP',
                'abstract': 'Procedures for creating, modifying, and deleting user accounts.',
                'call_number': 'SOP.005.8',
                'pages': 90,
            },
            {
                'title': 'Software Deployment Procedures',
                'abstract': 'Standard operating procedures for deploying software applications.',
                'call_number': 'SOP.005.1',
                'pages': 140,
            },
            {
                'title': 'Hardware Asset Management SOP',
                'abstract': 'Procedures for tracking and managing IT hardware assets.',
                'call_number': 'SOP.004.068',
                'pages': 110,
            },
            {
                'title': 'Email Security Procedures',
                'abstract': 'Standard procedures for maintaining email system security.',
                'call_number': 'SOP.005.8',
                'pages': 95,
            },
        ]

        for idx, sop_data in enumerate(sops, 1):
            author, _ = Author.objects.get_or_create(
                first_name='Operations',
                last_name=f'Team{idx}',
                defaults={'bio': 'Operations and compliance specialist'}
            )

            pub, created = Publication.objects.get_or_create(
                call_number=sop_data['call_number'] + f'.{idx:03d}',
                defaults={
                    'title': sop_data['title'],
                    'publication_type': pub_type,
                    'publisher': publisher,
                    'publication_date': datetime(2022 + idx % 3, (idx % 12) + 1, 1).date(),
                    'language': 'English',
                    'pages': sop_data['pages'],
                    'call_number': sop_data['call_number'] + f'.{idx:03d}',
                    'abstract': sop_data['abstract'],
                }
            )

            if created:
                pub.authors.add(author)
                pub.subjects.add(*random.sample(subjects, 2))

                for i in range(2):
                    Item.objects.create(
                        publication=pub,
                        barcode=f'SOP{idx:03d}{i+1:02d}',
                        location=location,
                        status='available',
                        condition='excellent'
                    )

        self.stdout.write(self.style.SUCCESS(f'Created {len(sops)} SOPs'))

    def create_capstone_projects(self):
        """Create sample Capstone Projects"""
        pub_type, _ = PublicationType.objects.get_or_create(
            code='CAP',
            defaults={'name': 'Capstone Project', 'description': 'Student capstone and thesis projects'}
        )

        publisher, _ = Publisher.objects.get_or_create(
            name='Academic Research Archives',
            defaults={'website': 'https://research.example.edu'}
        )

        location, _ = Location.objects.get_or_create(
            code='ARCH',
            defaults={'name': 'Archives', 'description': 'Academic archives', 'is_physical': True}
        )

        subjects_list = [
            'Research', 'Computer Science', 'Information Technology',
            'Software Development', 'Data Analysis', 'Machine Learning'
        ]

        subjects = []
        for subject_name in subjects_list:
            subject, _ = Subject.objects.get_or_create(name=subject_name)
            subjects.append(subject)

        projects = [
            {
                'title': 'Predictive Analytics for Customer Behavior',
                'abstract': 'Machine learning application for predicting customer purchasing patterns.',
                'call_number': 'CAP.2024.001',
                'pages': 85,
            },
            {
                'title': 'Mobile Application for Library Management',
                'abstract': 'Cross-platform mobile application for library catalog and circulation.',
                'call_number': 'CAP.2024.002',
                'pages': 92,
            },
            {
                'title': 'Blockchain-Based Supply Chain Tracking',
                'abstract': 'Implementation of blockchain technology for supply chain transparency.',
                'call_number': 'CAP.2024.003',
                'pages': 78,
            },
            {
                'title': 'AI-Powered Chatbot for Customer Service',
                'abstract': 'Natural language processing chatbot for automated customer support.',
                'call_number': 'CAP.2024.004',
                'pages': 88,
            },
            {
                'title': 'IoT-Based Smart Home Automation System',
                'abstract': 'Internet of Things platform for home automation and monitoring.',
                'call_number': 'CAP.2024.005',
                'pages': 95,
            },
            {
                'title': 'Cybersecurity Threat Detection System',
                'abstract': 'Real-time threat detection using machine learning algorithms.',
                'call_number': 'CAP.2024.006',
                'pages': 102,
            },
            {
                'title': 'E-Commerce Platform with Recommendation Engine',
                'abstract': 'Online shopping platform with personalized product recommendations.',
                'call_number': 'CAP.2024.007',
                'pages': 110,
            },
            {
                'title': 'Cloud-Based Document Management System',
                'abstract': 'Secure cloud platform for enterprise document management.',
                'call_number': 'CAP.2024.008',
                'pages': 87,
            },
            {
                'title': 'Real-Time Traffic Monitoring and Analysis',
                'abstract': 'Computer vision system for traffic pattern analysis and prediction.',
                'call_number': 'CAP.2024.009',
                'pages': 96,
            },
            {
                'title': 'Healthcare Patient Management System',
                'abstract': 'Integrated system for managing patient records and appointments.',
                'call_number': 'CAP.2024.010',
                'pages': 105,
            },
        ]

        for idx, project_data in enumerate(projects, 1):
            author, _ = Author.objects.get_or_create(
                first_name=f'Student{idx}',
                last_name=f'Researcher{idx}',
                defaults={'bio': 'Graduate student and researcher'}
            )

            pub, created = Publication.objects.get_or_create(
                call_number=project_data['call_number'],
                defaults={
                    'title': project_data['title'],
                    'publication_type': pub_type,
                    'publisher': publisher,
                    'publication_date': datetime(2024, (idx % 12) + 1, 1).date(),
                    'language': 'English',
                    'pages': project_data['pages'],
                    'call_number': project_data['call_number'],
                    'abstract': project_data['abstract'],
                }
            )

            if created:
                pub.authors.add(author)
                pub.subjects.add(*random.sample(subjects, 3))

                Item.objects.create(
                    publication=pub,
                    barcode=f'CAP{idx:04d}01',
                    location=location,
                    status='available',
                    condition='excellent'
                )

        self.stdout.write(self.style.SUCCESS(f'Created {len(projects)} Capstone Projects'))

    def create_ttps(self):
        """Create sample TTPs (Tactics, Techniques, and Procedures)"""
        pub_type, _ = PublicationType.objects.get_or_create(
            code='TTP',
            defaults={'name': 'TTP', 'description': 'Tactics, Techniques, and Procedures'}
        )

        publisher, _ = Publisher.objects.get_or_create(
            name='Security Research Institute',
            defaults={'website': 'https://securityresearch.example.org'}
        )

        location, _ = Location.objects.get_or_create(
            code='SEC',
            defaults={'name': 'Security Section', 'description': 'Security documentation', 'is_physical': True}
        )

        subjects_list = [
            'Cybersecurity', 'Threat Intelligence', 'Network Security',
            'Penetration Testing', 'Incident Response', 'Forensics'
        ]

        subjects = []
        for subject_name in subjects_list:
            subject, _ = Subject.objects.get_or_create(name=subject_name)
            subjects.append(subject)

        ttps = [
            {
                'title': 'Advanced Persistent Threat Detection Techniques',
                'abstract': 'Methods for identifying and mitigating APT campaigns.',
                'call_number': 'TTP.005.8.APT',
                'pages': 220,
            },
            {
                'title': 'Phishing Attack Analysis and Prevention',
                'abstract': 'Comprehensive guide to recognizing and preventing phishing attacks.',
                'call_number': 'TTP.005.8.PHI',
                'pages': 180,
            },
            {
                'title': 'Malware Reverse Engineering Procedures',
                'abstract': 'Techniques for analyzing and reverse engineering malicious software.',
                'call_number': 'TTP.005.8.MAL',
                'pages': 250,
            },
            {
                'title': 'Network Intrusion Detection Tactics',
                'abstract': 'Strategies for detecting and responding to network intrusions.',
                'call_number': 'TTP.004.6.IDS',
                'pages': 200,
            },
            {
                'title': 'Web Application Security Testing',
                'abstract': 'Methodologies for penetration testing web applications.',
                'call_number': 'TTP.005.8.WEB',
                'pages': 190,
            },
            {
                'title': 'Digital Forensics Investigation Techniques',
                'abstract': 'Procedures for collecting and analyzing digital evidence.',
                'call_number': 'TTP.005.8.FOR',
                'pages': 280,
            },
            {
                'title': 'Social Engineering Defense Strategies',
                'abstract': 'Methods for protecting against social engineering attacks.',
                'call_number': 'TTP.005.8.SOC',
                'pages': 160,
            },
            {
                'title': 'Wireless Network Security Procedures',
                'abstract': 'Techniques for securing wireless network infrastructure.',
                'call_number': 'TTP.004.6.WLS',
                'pages': 170,
            },
            {
                'title': 'Ransomware Response and Recovery',
                'abstract': 'Tactics for responding to and recovering from ransomware attacks.',
                'call_number': 'TTP.005.8.RAN',
                'pages': 150,
            },
            {
                'title': 'Cloud Security Assessment Methods',
                'abstract': 'Procedures for evaluating cloud infrastructure security.',
                'call_number': 'TTP.004.678.CLD',
                'pages': 210,
            },
        ]

        for idx, ttp_data in enumerate(ttps, 1):
            author1, _ = Author.objects.get_or_create(
                first_name='Security',
                last_name=f'Analyst{idx}',
                defaults={'bio': 'Cybersecurity specialist and threat researcher'}
            )

            pub, created = Publication.objects.get_or_create(
                call_number=ttp_data['call_number'],
                defaults={
                    'title': ttp_data['title'],
                    'publication_type': pub_type,
                    'publisher': publisher,
                    'publication_date': datetime(2023 + idx % 2, (idx % 12) + 1, 1).date(),
                    'language': 'English',
                    'pages': ttp_data['pages'],
                    'call_number': ttp_data['call_number'],
                    'abstract': ttp_data['abstract'],
                }
            )

            if created:
                pub.authors.add(author1)
                pub.subjects.add(*random.sample(subjects, 3))

                for i in range(2):
                    Item.objects.create(
                        publication=pub,
                        barcode=f'TTP{idx:03d}{i+1:02d}',
                        location=location,
                        status='available',
                        condition='good'
                    )

        self.stdout.write(self.style.SUCCESS(f'Created {len(ttps)} TTPs'))
