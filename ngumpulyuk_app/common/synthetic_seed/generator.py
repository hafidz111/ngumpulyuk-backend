"""Generate synthetic NgumpulYuk data with denormalized counters reconciled at the end."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import connection, transaction
from django.db.models import Count, Q
from django.utils import timezone

from ngumpulyuk_app.communities.models import Community, CommunityMember
from ngumpulyuk_app.discussions.models import Comment, Like, Thread
from ngumpulyuk_app.events.models import Event, EventParticipant, EventTag
from ngumpulyuk_app.notifications.models import Notification
from ngumpulyuk_app.recommendations.models import AiRecommendation, RecommendationSignal
from ngumpulyuk_app.users.models import ActivityHistory, UserInterest, UserPreferences
from ngumpulyuk_app.common.indonesia_locations import (
    all_locations as _all_indonesia_locations,
    location_coords,
    location_label,
    resolve_location,
)

from .constants import (
    COMMENT_SNIPPETS,
    COMMUNITY_CATEGORIES,
    COMMUNITY_DESCRIPTIONS,
    COMMUNITY_NAMES,
    COMMUNITY_THREAD_BODIES,
    EVENT_CATEGORIES,
    EVENT_DATE_MIN,
    EVENT_DESCRIPTIONS,
    EVENT_TITLES,
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_MALE,
    GLOBAL_THREAD_BODIES,
    GLOBAL_THREAD_COUNT,
    GLOBAL_THREAD_TITLES,
    INTERESTS,
    LAST_NAMES,
    LOCATIONS,
    PREFERRED_DAYS,
    PREFERRED_TIMES,
    REFERENCE_TODAY,
    STREET_NAMES,
    SYNTHETIC_EMAIL_DOMAIN,
    SYNTHETIC_PASSWORD,
    THREAD_TITLES,
)

User = get_user_model()

BATCH = 500


class SyntheticSeedGenerator:
    def __init__(
        self,
        *,
        user_count: int = 420,
        event_count: int = 210,
        community_count: int = 55,
        global_thread_count: int = GLOBAL_THREAD_COUNT,
        seed: int = 42,
    ):
        self.user_count = user_count
        self.event_count = event_count
        self.community_count = community_count
        self.global_thread_count = global_thread_count
        self.rng = random.Random(seed)
        self.today = date.fromisoformat(REFERENCE_TODAY)
        self.event_min = date.fromisoformat(EVENT_DATE_MIN)
        self.users: list = []
        self.events: list[Event] = []
        self.communities: list[Community] = []
        self.threads: list[Thread] = []
        self.global_threads: list[Thread] = []

    def _event_cover_url(self, index: int) -> str:
        return f"https://picsum.photos/seed/ngumpul-ev-{index}/900/500"

    def _community_cover_url(self, index: int) -> str:
        return f"https://picsum.photos/seed/ngumpul-com-{index}/800/400"

    def _community_logo_url(self, index: int) -> str:
        return f"https://picsum.photos/seed/ngumpul-logo-{index}/200/200"

    def _thread_image_url(self, seed_key: str) -> str:
        return f"https://picsum.photos/seed/{seed_key}/600/400"

    def _coords_for_area(self, area: str) -> tuple[Decimal, Decimal]:
        center = location_coords(area) or location_coords("3171") or (-6.2088, 106.8456)
        lat = center[0] + self.rng.uniform(-0.025, 0.025)
        lng = center[1] + self.rng.uniform(-0.025, 0.025)
        return Decimal(f"{lat:.6f}"), Decimal(f"{lng:.6f}")

    def _pick_location(self) -> tuple[str, str]:
        """Return (kemendagri_id, label) for events/users."""
        row = self.rng.choice(_all_indonesia_locations())
        return row["id"], row["label"]

    def _street_address(self, area: str) -> str:
        return f"Jl. {self.rng.choice(STREET_NAMES)} No. {self.rng.randint(1, 120)}, {area}"

    def _casual_topic(self) -> str:
        return self.rng.choice(
            [
                "futsal",
                "lari",
                "yoga",
                "badminton",
                "board game",
                "kopi",
                "musik live",
                "voli",
                "sepeda",
                "hiking",
            ]
        )

    def _global_thread_copy(self) -> tuple[str, str]:
        area = self.rng.choice(LOCATIONS)
        topic = self._casual_topic()
        title = self.rng.choice(GLOBAL_THREAD_TITLES).format(area=area, topic=topic)[:200]
        content = self.rng.choice(GLOBAL_THREAD_BODIES).format(area=area, topic=topic)
        return title, content

    def _community_thread_copy(self, community: Community) -> tuple[str | None, str]:
        area = self.rng.choice(LOCATIONS)
        topic = (community.category or "ngumpul").lower()
        title = self.rng.choice(THREAD_TITLES).format(area=area, topic=topic)[:200]
        content = self.rng.choice(COMMUNITY_THREAD_BODIES).format(area=area, topic=topic)
        if self.rng.random() < 0.12:
            return None, content
        return title, content

    def run(self) -> dict:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = 0")
                cursor.execute("SET LOCAL lock_timeout = '120s'")
            self._create_users()
            self._create_communities()
            self._create_events()
            self._create_memberships()
            self._create_discussions()
            self._create_notifications_and_recommendations()
            self._reconcile_denormalized_counts()
            self._create_activity_history()
        return self.summary()

    def summary(self) -> dict:
        return {
            "users": len(self.users),
            "events": len(self.events),
            "communities": len(self.communities),
            "threads": len(self.threads),
            "global_threads": len(self.global_threads),
            "participants": EventParticipant.objects.filter(
                user__email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}"
            ).count(),
            "community_members": CommunityMember.objects.filter(
                user__email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}"
            ).count(),
            "comments": Comment.objects.filter(
                author__email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}"
            ).count(),
            "likes": Like.objects.filter(
                user__email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}"
            ).count(),
        }

    def _pick_name(self) -> tuple[str, str, str]:
        gender = self.rng.choice(["male", "female", "other"])
        if gender == "male":
            first = self.rng.choice(FIRST_NAMES_MALE)
        elif gender == "female":
            first = self.rng.choice(FIRST_NAMES_FEMALE)
        else:
            first = self.rng.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
        last = self.rng.choice(LAST_NAMES)
        return f"{first} {last}", first.lower(), gender

    def _create_users(self) -> None:
        password_hash = make_password(SYNTHETIC_PASSWORD)
        rows = []
        for i in range(1, self.user_count + 1):
            full_name, slug, gender = self._pick_name()
            _loc_id, location = self._pick_location()
            age_years = self.rng.randint(20, 42)
            dob = self.today - timedelta(days=age_years * 365 + self.rng.randint(0, 364))
            rows.append(
                User(
                    email=f"syn{i:04d}@{SYNTHETIC_EMAIL_DOMAIN}",
                    username=f"syn_{i:04d}",
                    password=password_hash,
                    full_name=full_name,
                    phone=f"08{self.rng.randint(11, 99)}{self.rng.randint(10000000, 99999999)}",
                    date_of_birth=dob,
                    gender=gender,
                    bio=self.rng.choice(
                        [
                            f"Suka ngumpul di {location}.",
                            "Aktif ikut event akhir pekan.",
                            "Mencari komunitas yang asik dan inklusif.",
                            "Pemula yang semangat belajar bareng.",
                            None,
                        ]
                    ),
                    profile_picture=None,
                    location=location,
                    onboarding_completed=True,
                    is_verified=self.rng.random() < 0.15,
                    is_active=True,
                )
            )
        User.objects.bulk_create(rows, batch_size=BATCH)
        self.users = list(
            User.objects.filter(email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}").order_by("email")
        )

        pref_rows = []
        interest_rows = []
        for u in self.users:
            picks = self.rng.sample(INTERESTS, k=self.rng.randint(3, 6))
            for name in picks:
                interest_rows.append(UserInterest(user=u, interest_name=name))
            pref_rows.append(
                UserPreferences(
                    user=u,
                    preferred_days=self.rng.sample(
                        PREFERRED_DAYS, k=self.rng.randint(2, 4)
                    ),
                    preferred_time=self.rng.choice(PREFERRED_TIMES),
                    preferred_location=u.location,
                    notification_enabled=True,
                    email_notification=self.rng.random() < 0.85,
                    push_notification=self.rng.random() < 0.7,
                )
            )
        UserPreferences.objects.bulk_create(pref_rows, batch_size=BATCH)
        UserInterest.objects.bulk_create(interest_rows, batch_size=BATCH)

    def _create_communities(self) -> None:
        creators = self.rng.sample(self.users, k=min(len(self.users), self.community_count))
        for i in range(self.community_count):
            cat = self.rng.choice(COMMUNITY_CATEGORIES)
            _loc_id, loc_label = self._pick_location()
            name_tpl = self.rng.choice(COMMUNITY_NAMES)
            name = name_tpl.format(cat=cat, area=loc_label)[:100]
            creator = creators[i % len(creators)]
            c = Community.objects.create(
                name=name,
                description=self.rng.choice(COMMUNITY_DESCRIPTIONS).format(
                    cat=cat.lower(), area=loc_label
                ),
                category=cat,
                cover_image=self._community_cover_url(i),
                logo=self._community_logo_url(i),
                creator=creator,
                is_verified=self.rng.random() < 0.12,
            )
            self.communities.append(c)

    def _event_status_for_date(self, event_date: date, end_date: date | None) -> str:
        end = end_date or event_date
        if self.rng.random() < 0.03:
            return "cancelled"
        if end < self.today:
            return "completed"
        if event_date <= self.today <= end:
            return "ongoing"
        return "upcoming"

    def _random_event_date(self) -> date:
        span = (self.today - self.event_min).days
        offset = self.rng.randint(0, span + 45)
        return self.event_min + timedelta(days=offset)

    def _create_events(self) -> None:
        pending_events: list[Event] = []
        for i in range(self.event_count):
            creator = self.rng.choice(self.users)
            cat = self.rng.choice(EVENT_CATEGORIES)
            loc_id, loc_label = self._pick_location()
            title_tpl = self.rng.choice(EVENT_TITLES)
            title = title_tpl.format(cat=cat, area=loc_label)[:200]
            event_date = self._random_event_date()
            multi_day = self.rng.random() < 0.18
            end_date = event_date + timedelta(days=self.rng.randint(0, 2)) if multi_day else None
            status = self._event_status_for_date(event_date, end_date)
            has_deadline = self.rng.random() < 0.35 and status == "upcoming"
            reg_deadline = None
            reg_deadline_time = None
            if has_deadline:
                reg_deadline = event_date - timedelta(days=self.rng.randint(1, 10))
                reg_deadline_time = time(self.rng.randint(8, 20), self.rng.choice([0, 30]))
            lat, lng = self._coords_for_area(loc_id)
            ev = Event(
                creator=creator,
                title=title,
                description=self.rng.choice(EVENT_DESCRIPTIONS),
                category=cat,
                cover_image=self._event_cover_url(i),
                event_date=event_date,
                event_time=time(self.rng.randint(6, 21), self.rng.choice([0, 30])),
                end_date=end_date,
                end_time=time(22, 0) if end_date else None,
                has_registration_deadline=has_deadline,
                registration_deadline=reg_deadline,
                registration_deadline_time=reg_deadline_time,
                location_area=loc_id,
                location_address=self._street_address(loc_label),
                latitude=lat,
                longitude=lng,
                max_participants=self.rng.choice([15, 20, 25, 30, 40, 50, 80, 100]),
                current_participants=0,
                is_competition=self.rng.random() < 0.22,
                difficulty_level=self.rng.choice(
                    ["beginner", "intermediate", "advanced", None]
                ),
                status=status,
            )
            if ev.is_competition and not ev.difficulty_level:
                ev.difficulty_level = self.rng.choice(["beginner", "intermediate", "advanced"])
            pending_events.append(ev)

        Event.objects.bulk_create(pending_events, batch_size=BATCH)
        self.events = list(
            Event.objects.filter(creator__email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}")
            .select_related("creator")
            .order_by("created_at")
        )
        tag_rows = []
        for ev in self.events:
            _loc_row = resolve_location(ev.location_area)
            area_token = (
                (_loc_row["label"] if _loc_row else ev.location_area) or "jakarta"
            ).split()[0].lower()
            for tag in self.rng.sample(
                [ev.category.lower(), area_token, "ngumpul", "weekend", "komunitas"],
                k=self.rng.randint(1, 3),
            ):
                tag_rows.append(EventTag(event_id=ev.id, tag_name=tag[:50]))
        EventTag.objects.bulk_create(tag_rows, batch_size=BATCH)

    def _create_memberships(self) -> None:
        cm_rows: list[CommunityMember] = []
        ep_rows: list[EventParticipant] = []
        seen_cm: set[tuple] = set()
        seen_ep: set[tuple] = set()

        for c in self.communities:
            member_pool = self.rng.sample(
                self.users,
                k=min(len(self.users), self.rng.randint(12, min(80, len(self.users)))),
            )
            if c.creator not in member_pool:
                member_pool[0] = c.creator
            for u in member_pool:
                key = (c.id, u.id)
                if key in seen_cm:
                    continue
                seen_cm.add(key)
                role = (
                    "admin"
                    if u.id == c.creator_id
                    else self.rng.choices(["member", "moderator"], weights=[9, 1], k=1)[0]
                )
                cm_rows.append(CommunityMember(community_id=c.id, user_id=u.id, role=role))

        for ev in self.events:
            cap = ev.max_participants
            join_n = self.rng.randint(
                0, min(cap + 8, max(3, int(cap * self.rng.uniform(0.35, 1.05))))
            )
            joiners = self.rng.sample(self.users, k=min(join_n, len(self.users)))
            confirmed = 0
            for u in joiners:
                key = (ev.id, u.id)
                if key in seen_ep:
                    continue
                seen_ep.add(key)
                if confirmed >= cap and self.rng.random() < 0.7:
                    status = "waitlist"
                    attendance = None
                elif self.rng.random() < 0.04:
                    status = "cancelled"
                    attendance = None
                else:
                    status = "confirmed"
                    confirmed += 1
                    attendance = None
                    if ev.status == "completed":
                        attendance = self.rng.choices(
                            ["attended", "no_show", None],
                            weights=[75, 12, 13],
                            k=1,
                        )[0]
                ep_rows.append(
                    EventParticipant(
                        event_id=ev.id,
                        user_id=u.id,
                        status=status,
                        attendance_status=attendance,
                    )
                )

        CommunityMember.objects.bulk_create(cm_rows, batch_size=BATCH, ignore_conflicts=True)
        EventParticipant.objects.bulk_create(ep_rows, batch_size=BATCH, ignore_conflicts=True)

    def _create_discussions(self) -> None:
        thread_rows: list[Thread] = []

        for i in range(self.global_thread_count):
            author = self.rng.choice(self.users)
            title, content = self._global_thread_copy()
            related = None
            if self.rng.random() < 0.35 and self.events:
                related = self.rng.choice(self.events)
            thread_rows.append(
                Thread(
                    community_id=None,
                    related_event_id=related.id if related else None,
                    author_id=author.id,
                    title=title,
                    content=content,
                    images=[self._thread_image_url(f"ngumpul-global-{i}")],
                    like_count=0,
                    comment_count=0,
                    is_pinned=self.rng.random() < 0.04,
                )
            )

        for c in self.communities:
            n_threads = self.rng.randint(8, 22)
            for _ in range(n_threads):
                author = self.rng.choice(self.users)
                title, content = self._community_thread_copy(c)
                related = None
                if self.rng.random() < 0.25 and self.events:
                    related = self.rng.choice(self.events)
                thread_rows.append(
                    Thread(
                        community_id=c.id,
                        related_event_id=related.id if related else None,
                        author_id=author.id,
                        title=title,
                        content=content,
                        images=[self._thread_image_url(f"ngumpul-ct-{c.id}-{len(thread_rows)}")],
                        like_count=0,
                        comment_count=0,
                        is_pinned=self.rng.random() < 0.06,
                    )
                )

        Thread.objects.bulk_create(thread_rows, batch_size=BATCH)
        domain = f"@{SYNTHETIC_EMAIL_DOMAIN}"
        self.threads = list(
            Thread.objects.filter(author__email__endswith=domain)
            .exclude(community_id__isnull=True)
            .order_by("created_at")
        )
        self.global_threads = list(
            Thread.objects.filter(author__email__endswith=domain, community_id__isnull=True).order_by(
                "-created_at"
            )
        )

        all_threads = self.threads + self.global_threads

        comment_rows: list[Comment] = []
        for th in all_threads:
            n_comments = self.rng.randint(3, 14)
            for _ in range(n_comments):
                area = self.rng.choice(LOCATIONS)
                snippet = self.rng.choice(COMMENT_SNIPPETS).format(area=area)
                comment_rows.append(
                    Comment(
                        thread_id=th.id,
                        author_id=self.rng.choice(self.users).id,
                        content=snippet,
                        like_count=0,
                    )
                )
        Comment.objects.bulk_create(comment_rows, batch_size=BATCH)
        comments = list(
            Comment.objects.filter(thread_id__in=[t.id for t in all_threads])
        )

        like_rows: list[Like] = []
        seen_likes: set[tuple] = set()
        for th in all_threads:
            likers = self.rng.sample(
                self.users, k=min(len(self.users), self.rng.randint(2, 35))
            )
            for u in likers:
                key = (u.id, "thread", th.id)
                if key in seen_likes:
                    continue
                seen_likes.add(key)
                like_rows.append(
                    Like(user_id=u.id, likeable_type="thread", likeable_id=th.id)
                )
        for cm in comments:
            likers = self.rng.sample(
                self.users, k=min(len(self.users), self.rng.randint(0, 12))
            )
            for u in likers:
                key = (u.id, "comment", cm.id)
                if key in seen_likes:
                    continue
                seen_likes.add(key)
                like_rows.append(
                    Like(user_id=u.id, likeable_type="comment", likeable_id=cm.id)
                )
        Like.objects.bulk_create(like_rows, batch_size=BATCH, ignore_conflicts=True)

    def _create_notifications_and_recommendations(self) -> None:
        notif_rows = []
        upcoming = [e for e in self.events if e.status == "upcoming"][:40]
        for ev in upcoming:
            parts = EventParticipant.objects.filter(event_id=ev.id, status="confirmed")[:8]
            for p in parts:
                notif_rows.append(
                    Notification(
                        user_id=p.user_id,
                        type="event_reminder",
                        title=f"Reminder: {ev.title[:80]}",
                        message=f"Event kamu di {ev.location_area} sebentar lagi.",
                        related_id=ev.id,
                        is_read=self.rng.random() < 0.4,
                    )
                )
        for _ in range(120):
            u = self.rng.choice(self.users)
            notif_rows.append(
                Notification(
                    user_id=u.id,
                    type=self.rng.choice(
                        ["new_event", "community_post", "comment_reply", "new_member"]
                    ),
                    title="Update dari NgumpulYuk",
                    message="Ada aktivitas baru di komunitas kamu.",
                    is_read=self.rng.random() < 0.55,
                )
            )
        Notification.objects.bulk_create(notif_rows, batch_size=BATCH)

        ai_rows = []
        sig_rows = []
        expires = timezone.now() + timedelta(days=7)
        for u in self.rng.sample(self.users, k=min(80, len(self.users))):
            for ev in self.rng.sample(self.events, k=min(5, len(self.events))):
                ai_rows.append(
                    AiRecommendation(
                        user_id=u.id,
                        event_id=ev.id,
                        score=Decimal(str(round(self.rng.uniform(55, 98), 2))),
                        reason=f"Cocok dengan minat {ev.category} di {ev.location_area}.",
                        expires_at=expires,
                    )
                )
                sig_rows.append(
                    RecommendationSignal(
                        user_id=u.id,
                        event_id=ev.id,
                        signal_type=self.rng.choice(["view", "like", "join", "save"]),
                        platform=self.rng.choice(["web", "android", "ios"]),
                        source="synthetic_seed",
                    )
                )
        AiRecommendation.objects.bulk_create(ai_rows, batch_size=BATCH, ignore_conflicts=True)
        RecommendationSignal.objects.bulk_create(sig_rows, batch_size=BATCH)

    def _reconcile_denormalized_counts(self) -> None:
        for c in Community.objects.filter(
            creator__email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}"
        ).annotate(mc=Count("memberships")):
            if c.member_count != c.mc:
                Community.objects.filter(pk=c.pk).update(member_count=c.mc)

        for ev in Event.objects.filter(
            creator__email__endswith=f"@{SYNTHETIC_EMAIL_DOMAIN}"
        ).annotate(
            cp=Count("participants", filter=Q(participants__status="confirmed"))
        ):
            if ev.current_participants != ev.cp:
                Event.objects.filter(pk=ev.pk).update(current_participants=ev.cp)

        all_threads = self.threads + self.global_threads
        thread_ids = [t.id for t in all_threads]
        thread_like_counts = {
            row["likeable_id"]: row["c"]
            for row in Like.objects.filter(likeable_type="thread")
            .values("likeable_id")
            .annotate(c=Count("id"))
        }
        thread_comment_counts = {
            row["thread_id"]: row["c"]
            for row in Comment.objects.filter(thread_id__in=thread_ids)
            .values("thread_id")
            .annotate(c=Count("id"))
        }
        threads_to_update = []
        for th in all_threads:
            th.like_count = thread_like_counts.get(th.id, 0)
            th.comment_count = thread_comment_counts.get(th.id, 0)
            threads_to_update.append(th)
        Thread.objects.bulk_update(
            threads_to_update, ["like_count", "comment_count"], batch_size=BATCH
        )

        comment_ids = list(
            Comment.objects.filter(thread_id__in=thread_ids).values_list("id", flat=True)
        )
        comment_like_counts = {
            row["likeable_id"]: row["c"]
            for row in Like.objects.filter(
                likeable_type="comment", likeable_id__in=comment_ids
            )
            .values("likeable_id")
            .annotate(c=Count("id"))
        }
        comments = list(
            Comment.objects.filter(id__in=comment_ids).only("id", "like_count")
        )
        for cm in comments:
            cm.like_count = comment_like_counts.get(cm.id, 0)
        Comment.objects.bulk_update(comments, ["like_count"], batch_size=BATCH)

    def _create_activity_history(self) -> None:
        rows: list[ActivityHistory] = []
        domain = f"@{SYNTHETIC_EMAIL_DOMAIN}"

        for ev in self.events:
            if ev.creator.email.endswith(domain):
                rows.append(
                    ActivityHistory(
                        user_id=ev.creator_id,
                        activity_type="created_event",
                        description=f"Created event: {ev.title}",
                        related_type="event",
                        related_id=ev.id,
                    )
                )

        for c in self.communities:
            rows.append(
                ActivityHistory(
                    user_id=c.creator_id,
                    activity_type="created_community",
                    description=f"Created community: {c.name}",
                    related_type="community",
                    related_id=c.id,
                )
            )

        for ep in EventParticipant.objects.filter(
            user__email__endswith=domain, status="confirmed"
        ).select_related("event"):
            rows.append(
                ActivityHistory(
                    user_id=ep.user_id,
                    activity_type="joined_event",
                    description=f"Joined event: {ep.event.title}",
                    related_type="event",
                    related_id=ep.event_id,
                )
            )
            end = ep.event.end_date or ep.event.event_date
            if end < self.today and ep.attendance_status == "attended":
                rows.append(
                    ActivityHistory(
                        user_id=ep.user_id,
                        activity_type="attended_event",
                        description=f"Attended event: {ep.event.title}",
                        related_type="event",
                        related_id=ep.event_id,
                    )
                )

        for cm in CommunityMember.objects.filter(user__email__endswith=domain).select_related(
            "community"
        ):
            if cm.user_id == cm.community.creator_id:
                continue
            rows.append(
                ActivityHistory(
                    user_id=cm.user_id,
                    activity_type="joined_community",
                    description=f"Joined community: {cm.community.name}",
                    related_type="community",
                    related_id=cm.community_id,
                )
            )

        for th in self.threads + self.global_threads:
            rows.append(
                ActivityHistory(
                    user_id=th.author_id,
                    activity_type="posted_thread",
                    description=(
                        "Posted thread in global feed"
                        if th.community_id is None
                        else "Posted a thread"
                    ),
                    related_type="thread",
                    related_id=th.id,
                )
            )

        comment_ids = list(
            Comment.objects.filter(author__email__endswith=domain).values_list(
                "id", "author_id", "thread_id"
            )[:2500]
        )
        for _cid, author_id, thread_id in comment_ids:
            rows.append(
                ActivityHistory(
                    user_id=author_id,
                    activity_type="commented",
                    description="Posted a comment",
                    related_type="thread",
                    related_id=thread_id,
                )
            )

        ActivityHistory.objects.bulk_create(rows, batch_size=BATCH)


def _coords_for_rng(rng: random.Random, area: str) -> tuple[Decimal, Decimal]:
    center = location_coords(area) or (-6.2088, 106.8456)
    lat = center[0] + rng.uniform(-0.025, 0.025)
    lng = center[1] + rng.uniform(-0.025, 0.025)
    return Decimal(f"{lat:.6f}"), Decimal(f"{lng:.6f}")


def _casual_topic_for_rng(rng: random.Random) -> str:
    return rng.choice(
        [
            "futsal",
            "lari",
            "yoga",
            "badminton",
            "board game",
            "kopi",
            "musik live",
            "voli",
            "sepeda",
            "hiking",
        ]
    )


def _global_thread_copy_for_rng(rng: random.Random) -> tuple[str, str]:
    area = rng.choice(LOCATIONS)
    topic = _casual_topic_for_rng(rng)
    title = rng.choice(GLOBAL_THREAD_TITLES).format(area=area, topic=topic)[:200]
    content = rng.choice(GLOBAL_THREAD_BODIES).format(area=area, topic=topic)
    return title, content


def _community_thread_copy_for_rng(
    rng: random.Random, community: Community
) -> tuple[str | None, str]:
    area = rng.choice(LOCATIONS)
    topic = (community.category or "ngumpul").lower()
    title = rng.choice(THREAD_TITLES).format(area=area, topic=topic)[:200]
    content = rng.choice(COMMUNITY_THREAD_BODIES).format(area=area, topic=topic)
    if rng.random() < 0.12:
        return None, content
    return title, content


def patch_synthetic_copy_and_coords(*, seed: int = 42) -> dict:
    """Rewrite synthetic thread copy and fix event lat/lng to match location_area."""
    rng = random.Random(seed)
    domain = f"@{SYNTHETIC_EMAIL_DOMAIN}"

    events = list(Event.objects.filter(creator__email__endswith=domain))
    for ev in events:
        row = resolve_location(ev.location_area)
        if not row:
            picked = rng.choice(_all_indonesia_locations())
            row = picked
        loc_id = row["id"]
        loc_label = row["label"]
        lat, lng = _coords_for_rng(rng, loc_id)
        ev.location_area = loc_id
        ev.latitude = lat
        ev.longitude = lng
        ev.location_address = f"Jl. {rng.choice(STREET_NAMES)} No. {rng.randint(1, 120)}, {loc_label}"
    if events:
        Event.objects.bulk_update(
            events,
            ["location_area", "latitude", "longitude", "location_address"],
            batch_size=BATCH,
        )

    threads = list(
        Thread.objects.filter(author__email__endswith=domain).select_related("community")
    )
    for th in threads:
        if th.community_id is None:
            title, content = _global_thread_copy_for_rng(rng)
        else:
            title, content = _community_thread_copy_for_rng(rng, th.community)
        th.title = title
        th.content = content
    if threads:
        Thread.objects.bulk_update(threads, ["title", "content"], batch_size=BATCH)

    return {"events_updated": len(events), "threads_updated": len(threads)}


def patch_synthetic_media() -> dict:
    """Backfill cover/logo images on existing synthetic rows (no user delete)."""
    domain = f"@{SYNTHETIC_EMAIL_DOMAIN}"
    events_qs = Event.objects.filter(creator__email__endswith=domain).filter(
        Q(cover_image__isnull=True) | Q(cover_image="")
    )
    communities_qs = Community.objects.filter(creator__email__endswith=domain)
    communities_qs = communities_qs.filter(
        Q(cover_image__isnull=True)
        | Q(cover_image="")
        | Q(logo__isnull=True)
        | Q(logo="")
    )

    events_updated = 0
    for ev in events_qs.iterator():
        ev.cover_image = f"https://picsum.photos/seed/ngumpul-ev-{ev.id}/900/500"
        ev.save(update_fields=["cover_image"])
        events_updated += 1

    communities_updated = 0
    for c in communities_qs.iterator():
        updates = {}
        if not c.cover_image:
            updates["cover_image"] = f"https://picsum.photos/seed/ngumpul-com-{c.id}/800/400"
        if not c.logo:
            updates["logo"] = f"https://picsum.photos/seed/ngumpul-logo-{c.id}/200/200"
        if updates:
            Community.objects.filter(pk=c.pk).update(**updates)
            communities_updated += 1

    return {"events_updated": events_updated, "communities_updated": communities_updated}


def clear_synthetic_data() -> dict:
    """Remove synthetic users; related rows cascade via FK on_delete."""
    domain = f"@{SYNTHETIC_EMAIL_DOMAIN}"
    qs = User.objects.filter(email__endswith=domain)
    count = qs.count()
    if not count:
        return {"deleted_users": 0}
    deleted_total, _by_model = qs.delete()
    return {"deleted_users": count, "deleted_rows_total": deleted_total}
