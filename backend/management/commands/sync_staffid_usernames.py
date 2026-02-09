from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Sync a user model field (default "staff_id") into the username field. Safe: supports --dry-run and --force.'

    def add_arguments(self, parser):
        parser.add_argument('--field', default='staff_id', help='Source field on User to copy from (default: staff_id)')
        parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
        parser.add_argument('--force', action='store_true', help='Apply changes (must be used to write)')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of users to process (0 = all)')

    def handle(self, *args, **options):
        field = options['field']
        dry_run = options['dry_run']
        force = options['force']
        limit = options['limit']

        if not dry_run and not force:
            raise CommandError('This command is safe by default. Use --dry-run to preview or --force to apply changes.')

        User = get_user_model()
        qs = User.objects.all()
        # filter users that have non-empty value for the source field
        qs = [u for u in qs if getattr(u, field, None)]
        total = len(qs)
        if limit and limit > 0:
            qs = qs[:limit]

        self.stdout.write(f'Found {total} users with non-empty "{field}". Processing {len(qs)} users.')

        collisions = []
        updates = []

        existing_usernames = set(User.objects.values_list('username', flat=True))

        for u in qs:
            src = str(getattr(u, field)).strip()
            if not src:
                continue
            if u.username == src:
                continue
            # if another user already has that username (and it's not this user) report collision
            if src in existing_usernames and src != u.username:
                collisions.append((u.pk, u.username, src))
                continue
            updates.append((u.pk, u.username, src))

        if collisions:
            self.stdout.write('\nCollisions detected — these will be skipped:')
            for pk, cur, src in collisions:
                self.stdout.write(f'  pk={pk} current_username={cur!r} desired_username={src!r}')

        if not updates:
            self.stdout.write('\nNo users to update.')
            return

        self.stdout.write(f'\nPlanned updates ({len(updates)}):')
        for pk, cur, src in updates:
            self.stdout.write(f'  pk={pk} {cur!r} -> {src!r}')

        if dry_run:
            self.stdout.write('\nDry run complete. No changes made.')
            return

        # apply changes inside a transaction
        applied = 0
        with transaction.atomic():
            for pk, cur, src in updates:
                u = User.objects.filter(pk=pk).first()
                if not u:
                    continue
                # final collision check
                conflict = User.objects.filter(username=src).exclude(pk=pk).exists()
                if conflict:
                    self.stdout.write(f'SKIP pk={pk} conflict for username {src!r}')
                    continue
                u.username = src
                u.save()
                applied += 1

        self.stdout.write(f'\nApplied {applied} updates.')
