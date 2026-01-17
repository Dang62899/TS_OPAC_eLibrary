"""
Management command to add sample SVG cover images to publications
"""
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from catalog.models import Publication


class Command(BaseCommand):
    help = 'Add sample SVG cover images from media/books folder to publications'

    def handle(self, *args, **options):
        media_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'media', 'books')
        
        publications = Publication.objects.all().order_by('id')
        sample_covers = []
        
        # Get all sample SVG files
        for i in range(1, 30):
            svg_file = os.path.join(media_path, f'sample_{i}.svg')
            if os.path.exists(svg_file):
                sample_covers.append(svg_file)
        
        if not sample_covers:
            self.stdout.write(self.style.ERROR('No sample cover files found in media/books'))
            return
        
        self.stdout.write(f'Found {len(sample_covers)} sample cover files')
        
        # Assign covers to publications
        for idx, publication in enumerate(publications):
            # Cycle through available covers
            cover_idx = idx % len(sample_covers)
            cover_path = sample_covers[cover_idx]
            
            # Only update if cover_image is not already set
            if not publication.cover_image:
                with open(cover_path, 'rb') as f:
                    cover_name = f'covers/sample_{cover_idx + 1}.svg'
                    publication.cover_image.save(
                        cover_name,
                        ContentFile(f.read()),
                        save=False
                    )
                publication.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated publication {publication.id}: {publication.title[:50]}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully added covers to {publications.count()} publications')
        )
