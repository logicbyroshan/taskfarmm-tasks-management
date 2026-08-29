import time
from django.core.management.base import BaseCommand
from todo.notifications import NotificationService


class Command(BaseCommand):
    help = 'Processes queued outbound email notifications and retries failed deliveries with exponential backoff.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Maximum number of notifications to process in one batch.'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run continuously as a background worker loop.'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Polling interval in seconds when running in daemon mode.'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        is_daemon = options['daemon']
        interval = options['interval']

        self.stdout.write(self.style.SUCCESS('Starting TaskFarmm Notification Queue Processor...'))

        if is_daemon:
            self.stdout.write(f'Running as daemon (polling every {interval} seconds). Press Ctrl+C to stop.')
            try:
                while True:
                    result = NotificationService.process_queue(batch_size=batch_size)
                    if result['total_processed'] > 0:
                        self.stdout.write(
                            f"Processed {result['total_processed']} notifications (Succeeded: {result['succeeded']}, Failed: {result['failed']})"
                        )
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Daemon stopped by user.'))
        else:
            result = NotificationService.process_queue(batch_size=batch_size)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Queue processing complete. Processed: {result['total_processed']} (Succeeded: {result['succeeded']}, Failed: {result['failed']})"
                )
            )
