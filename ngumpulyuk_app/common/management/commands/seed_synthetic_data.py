from django.core.management.base import BaseCommand

from ngumpulyuk_app.common.synthetic_seed import (
    SyntheticSeedGenerator,
    clear_synthetic_data,
    patch_synthetic_copy_and_coords,
    patch_synthetic_media,
)
from ngumpulyuk_app.common.synthetic_seed.constants import (
    REFERENCE_TODAY,
    SYNTHETIC_EMAIL_DOMAIN,
    SYNTHETIC_PASSWORD,
)


class Command(BaseCommand):
    help = (
        "Inject synthetic members, events, communities, threads, likes, and comments. "
        f"Users use *@{SYNTHETIC_EMAIL_DOMAIN} (password: {SYNTHETIC_PASSWORD}). "
        f"Reference today: {REFERENCE_TODAY}."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help=f"Remove existing synthetic users (*@{SYNTHETIC_EMAIL_DOMAIN}) before seeding.",
        )
        parser.add_argument("--users", type=int, default=420, help="Number of member accounts.")
        parser.add_argument("--events", type=int, default=210, help="Number of events.")
        parser.add_argument(
            "--communities", type=int, default=55, help="Number of communities."
        )
        parser.add_argument(
            "--global-threads",
            type=int,
            default=200,
            help="Number of global feed threads (community=null).",
        )
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
        parser.add_argument(
            "--patch-media",
            action="store_true",
            help="Only backfill missing cover/logo images on existing synthetic data.",
        )
        parser.add_argument(
            "--patch-copy",
            action="store_true",
            help="Rewrite synthetic thread captions and fix event coordinates (no delete).",
        )

    def handle(self, *args, **options):
        if options["patch_copy"]:
            stats = patch_synthetic_copy_and_coords(seed=options["seed"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Patched copy/coords: events={stats['events_updated']} "
                    f"threads={stats['threads_updated']}"
                )
            )
            return

        if options["patch_media"]:
            stats = patch_synthetic_media()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Patched images: events={stats['events_updated']} "
                    f"communities={stats['communities_updated']}"
                )
            )
            return

        if options["clear"]:
            result = clear_synthetic_data()
            self.stdout.write(
                self.style.WARNING(f"Cleared synthetic data ({result['deleted_users']} user rows).")
            )

        generator = SyntheticSeedGenerator(
            user_count=options["users"],
            event_count=options["events"],
            community_count=options["communities"],
            global_thread_count=options["global_threads"],
            seed=options["seed"],
        )
        self.stdout.write(
            "Seeding synthetic data (stop runserver if inserts time out on remote DB)..."
        )
        stats = generator.run()
        self.stdout.write(self.style.SUCCESS("Synthetic seed completed."))
        self.stdout.write(
            f"  users={stats['users']} events={stats['events']} communities={stats['communities']}"
        )
        self.stdout.write(
            f"  threads={stats['threads']} global_threads={stats['global_threads']} "
            f"participants={stats['participants']} community_members={stats['community_members']}"
        )
        self.stdout.write(
            f"  comments={stats['comments']} likes={stats['likes']}"
        )
        self.stdout.write(
            f"Login example: syn0001@{SYNTHETIC_EMAIL_DOMAIN} / {SYNTHETIC_PASSWORD}"
        )
