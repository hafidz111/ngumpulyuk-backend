from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from ngumpulyuk_app.communities.models import Community
from ngumpulyuk_app.events.models import Event
from ngumpulyuk_app.chat.models import ChatAnswerCorrection, ChatTurn

User = get_user_model()


@override_settings(CHAT_LLM_ENABLED=False, CHAT_GEMINI_API_KEY=None)
class ChatApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="chat@test.com",
            full_name="Chat User",
            username="chatuser",
            password="x",
        )
        self.client.force_authenticate(user=self.user)

    def test_chat_requires_auth(self):
        c = APIClient()
        r = c.post("/api/v1/chat/", {"message": "hai"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_chat_greeting(self):
        r = self.client.post("/api/v1/chat/", {"message": "Halo!", "session_id": "s1"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data["success"])
        d = r.data["data"]
        self.assertEqual(d["intent"], "greeting")
        self.assertIn("trace_id", d)
        self.assertFalse(d["llm_used"])

    def test_feedback_flow(self):
        r = self.client.post("/api/v1/chat/", {"message": "Apa itu NgumpulYuk?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        tid = r.data["data"]["trace_id"]
        fr = self.client.post(
            "/api/v1/chat/feedback/",
            {"trace_id": tid, "helpful": True},
            format="json",
        )
        self.assertEqual(fr.status_code, status.HTTP_200_OK)

    def test_feedback_not_found(self):
        import uuid

        r = self.client.post(
            "/api/v1/chat/feedback/",
            {"trace_id": str(uuid.uuid4()), "helpful": False},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_event_keywords_use_event_intent(self):
        r = self.client.post("/api/v1/chat/", {"message": "ada acara apa minggu ini?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "event_reco")

    def test_event_query_does_not_fallback_to_community_cards(self):
        Community.objects.create(
            name="Mobile Legends Bang Bang",
            description="Ayoo main mobile legends",
            category="Gaming",
            creator=self.user,
        )
        r = self.client.post("/api/v1/chat/", {"message": "rekomendasi acara dong"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        cards = r.data["data"]["cards"]
        self.assertTrue(all(c["type"] != "community" for c in cards))

    def test_event_query_falls_back_to_keyword_search(self):
        creator = User.objects.create_user(
            email="creator2@test.com",
            full_name="Creator 2",
            username="creator2",
            password="x",
        )
        Event.objects.create(
            creator=creator,
            title="Fun Futsal Weekend",
            description="Main futsal bareng komunitas",
            category="Olahraga",
            event_date=date.today() + timedelta(days=2),
            event_time=time(19, 0),
            location_area="Jakarta Selatan",
            location_address="Lapangan A",
            max_participants=40,
            status="upcoming",
        )
        r = self.client.post("/api/v1/chat/", {"message": "Event olahraga minggu ini"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "event_reco")
        self.assertGreaterEqual(len(r.data["data"]["cards"]), 1)
        self.assertEqual(r.data["data"]["cards"][0]["type"], "event")
        self.assertIn("image_url", r.data["data"]["cards"][0])

    def test_community_card_contains_image_url_field(self):
        Community.objects.create(
            name="ML Bang Bang",
            description="Ayoo main mobile legends",
            category="Gaming",
            cover_image="https://example.com/community-cover.png",
            creator=self.user,
        )
        r = self.client.post("/api/v1/chat/", {"message": "komunitas gaming apa yang rame?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        cards = r.data["data"]["cards"]
        comm_cards = [c for c in cards if c["type"] == "community"]
        self.assertTrue(comm_cards)
        self.assertIn("image_url", comm_cards[0])

    def test_event_query_can_return_self_created_event_as_last_resort(self):
        Event.objects.create(
            creator=self.user,
            title="Latihan Futsal Internal",
            description="Sparring santai",
            category="Futsal",
            event_date=date.today() + timedelta(days=3),
            event_time=time(20, 0),
            location_area="Jakarta Selatan",
            location_address="Lapangan B",
            max_participants=20,
            status="upcoming",
        )
        r = self.client.post("/api/v1/chat/", {"message": "event olahraga minggu ini"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        event_cards = [c for c in r.data["data"]["cards"] if c["type"] == "event"]
        self.assertTrue(event_cards)

    def test_futsal_keyword_returns_event_cards(self):
        creator = User.objects.create_user(
            email="creator3@test.com",
            full_name="Creator 3",
            username="creator3",
            password="x",
        )
        Event.objects.create(
            creator=creator,
            title="Liga Futsal Jumat",
            description="Turnamen futsal santai",
            category="Futsal",
            event_date=date.today() + timedelta(days=4),
            event_time=time(18, 0),
            location_area="Bandung",
            location_address="GOR X",
            max_participants=30,
            status="upcoming",
        )
        r = self.client.post("/api/v1/chat/", {"message": "event futsal minggu ini"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "event_reco")
        event_cards = [c for c in r.data["data"]["cards"] if c["type"] == "event"]
        self.assertGreaterEqual(len(event_cards), 1)
        matched = False
        for c in event_cards:
            p = c["payload"]
            blob = f"{p.get('title', '')} {p.get('category', '')}".lower()
            if "futsal" in blob or "olahraga" in blob:
                matched = True
                break
        self.assertTrue(matched)

    def test_rekomendasi_keyword_returns_event_cards_when_available(self):
        Event.objects.create(
            creator=self.user,
            title="Ngumpul Santai",
            description="Hangout ringan",
            category="Social",
            event_date=date.today() + timedelta(days=5),
            event_time=time(15, 0),
            location_area="Jakarta",
            location_address="Cafe A",
            max_participants=20,
            status="upcoming",
        )
        r = self.client.post("/api/v1/chat/", {"message": "ada rekomendasi?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "event_reco")
        self.assertGreaterEqual(len([c for c in r.data["data"]["cards"] if c["type"] == "event"]), 1)

    def test_community_query_returns_community_cards(self):
        Community.objects.create(
            name="Komunitas Futsal Bandung",
            description="Main futsal tiap minggu",
            category="Olahraga",
            creator=self.user,
        )
        r = self.client.post(
            "/api/v1/chat/",
            {"message": "komunitas futsal apa yang bisa saya join?"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "community_reco")
        comm_cards = [c for c in r.data["data"]["cards"] if c["type"] == "community"]
        self.assertGreaterEqual(len(comm_cards), 1)

    def test_welcome_chip_nearby_not_generic_faq(self):
        creator = User.objects.create_user(
            email="creator5@test.com",
            full_name="Creator 5",
            username="creator5",
            password="x",
        )
        Event.objects.create(
            creator=creator,
            title="Ngumpul Senja Jakarta",
            description="Hangout santai",
            category="Social",
            event_date=date.today() + timedelta(days=3),
            event_time=time(17, 0),
            location_area="Jakarta Selatan",
            location_address="Kafe B",
            max_participants=30,
            status="upcoming",
        )
        r = self.client.post("/api/v1/chat/", {"message": "Ada yang deket aku?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "place_reco")
        self.assertNotIn("FAQ singkat", r.data["data"]["reply"])

    def test_active_community_chip(self):
        Community.objects.create(
            name="Komunitas Runner ID",
            description="Lari bareng tiap minggu",
            category="Olahraga",
            creator=self.user,
            member_count=120,
        )
        r = self.client.post(
            "/api/v1/chat/",
            {"message": "Komunitas yang aktif"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "community_reco")
        self.assertGreaterEqual(len([c for c in r.data["data"]["cards"] if c["type"] == "community"]), 1)

    def test_cara_daftar_returns_faq_not_generic(self):
        r = self.client.post("/api/v1/chat/", {"message": "Cara daftar gimana?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "faq")
        self.assertIn("akun", r.data["data"]["reply"].lower())
        self.assertNotIn("FAQ singkat", r.data["data"]["reply"])

    def test_creative_theme_query_returns_cards_not_generic_faq(self):
        creator = User.objects.create_user(
            email="creator4@test.com",
            full_name="Creator 4",
            username="creator4",
            password="x",
        )
        Event.objects.create(
            creator=creator,
            title="Workshop Seni Kreatif",
            description="Belajar lukis dan craft bareng",
            category="Seni",
            event_date=date.today() + timedelta(days=6),
            event_time=time(14, 0),
            location_area="Jakarta",
            location_address="Studio A",
            max_participants=25,
            status="upcoming",
        )
        Community.objects.create(
            name="Kreasi Jakarta",
            description="Komunitas seni dan desain kreatif",
            category="Kreatif",
            creator=creator,
        )
        r = self.client.post(
            "/api/v1/chat/",
            {"message": "Ada yang temanya kreatif?"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "event_reco")
        self.assertGreaterEqual(len(r.data["data"]["cards"]), 1)
        self.assertNotIn("FAQ singkat", r.data["data"]["reply"])

    def test_faq_query_does_not_return_cards(self):
        r = self.client.post("/api/v1/chat/", {"message": "Apa itu NgumpulYuk?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "faq")
        self.assertEqual(r.data["data"]["cards"], [])

    def test_admin_correction_overrides_reply(self):
        ChatAnswerCorrection.objects.create(
            normalized_query="web apa ini",
            corrected_reply="Ini platform NgumpulYuk buat cari event dan komunitas.",
            intent="faq",
            is_active=True,
        )
        r = self.client.post("/api/v1/chat/", {"message": "web apa ini"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["reply"], "Ini platform NgumpulYuk buat cari event dan komunitas.")
        self.assertTrue(r.data["data"]["correction_applied"])
        self.assertTrue(r.data["data"]["answer_source"]["type"].startswith("correction"))
        turn = ChatTurn.objects.get(pk=r.data["data"]["trace_id"])
        self.assertTrue(turn.correction_applied)
        self.assertEqual(turn.user_message_redacted, "web apa ini")

    def test_semantic_alias_reuses_canonical_what_is_answer(self):
        r = self.client.post("/api/v1/chat/", {"message": "web apa ini"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "general")
        self.assertIn("NgumpulYuk itu platform", r.data["data"]["reply"])


@override_settings(CHAT_LLM_ENABLED=False, CHAT_GEMINI_API_KEY=None)
class ChatAdminApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com",
            full_name="Admin",
            username="admin",
            password="x",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            email="member@test.com",
            full_name="Member",
            username="member",
            password="x",
        )

    def test_admin_can_create_and_list_corrections(self):
        self.client.force_authenticate(self.admin)
        cr = self.client.post(
            "/api/v1/admin/chat/corrections/",
            {
                "normalized_query": "web apa ini",
                "use_faq_id": "what-is",
                "intent": "faq"
            },
            format="json",
        )
        self.assertEqual(cr.status_code, status.HTTP_200_OK)
        self.assertEqual(cr.data["data"]["correction"]["source_type"], "faq")
        self.assertEqual(cr.data["data"]["correction"]["source_ref"], "what-is")
        ls = self.client.get("/api/v1/admin/chat/corrections/?intent=faq")
        self.assertEqual(ls.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(ls.data["data"]["items"]), 1)

    def test_admin_can_view_chat_logs(self):
        self.client.force_authenticate(self.user)
        self.client.post("/api/v1/chat/", {"message": "halo"}, format="json")
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/v1/admin/chat/logs/?limit=10")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(r.data["data"]["items"]), 1)

    def test_admin_can_delete_chat_logs(self):
        self.client.force_authenticate(self.user)
        self.client.post("/api/v1/chat/", {"message": "halo"}, format="json")
        self.client.post("/api/v1/chat/", {"message": "web apa ini"}, format="json")
        self.client.force_authenticate(self.admin)
        dr = self.client.delete("/api/v1/admin/chat/logs/", {"delete_all": True}, format="json")
        self.assertEqual(dr.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(dr.data["data"]["deleted_count"], 2)
        left = ChatTurn.objects.count()
        self.assertEqual(left, 0)

    def test_admin_can_get_faq_templates(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/v1/admin/chat/templates/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(r.data["data"]["count"], 1)
        ids = [t["id"] for t in r.data["data"]["templates"]]
        self.assertIn("what-is", ids)
        self.assertIn("ngumpsky", ids)
        self.assertIn("join-event", ids)
        self.assertGreaterEqual(r.data["data"]["count"], 20)


class FaqMatchTests(TestCase):
    def test_register_alias(self):
        from ngumpulyuk_app.chat.services.faq import match_faq

        hits = match_faq("cara daftar gimana?")
        self.assertEqual(hits[0]["id"], "account-register")

    def test_ngumpsky_alias(self):
        from ngumpulyuk_app.chat.services.faq import match_faq

        hits = match_faq("kamu siapa sih?")
        self.assertEqual(hits[0]["id"], "ngumpsky")

    def test_create_event_beats_generic_event_keyword(self):
        from ngumpulyuk_app.chat.services.faq import match_faq

        hits = match_faq("gimana bikin event sendiri")
        self.assertEqual(hits[0]["id"], "create-event")

    def test_answers_have_no_database_word(self):
        from ngumpulyuk_app.chat.services.faq import FAQ_ENTRIES

        for entry in FAQ_ENTRIES:
            self.assertNotIn(
                "database",
                entry["answer"].lower(),
                msg=entry["id"],
            )

    @override_settings(CHAT_LLM_ENABLED=False, CHAT_GEMINI_API_KEY=None)
    def test_chat_faq_ngumpsky_intent(self):
        client = APIClient()
        user = User.objects.create_user(
            email="faq@test.com",
            full_name="FAQ User",
            username="faquser",
            password="x",
        )
        client.force_authenticate(user=user)
        r = client.post("/api/v1/chat/", {"message": "Ngumpsky itu apa?"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["intent"], "faq")
        self.assertIn("ngumpsky", r.data["data"]["reply"].lower())
        self.assertNotIn("database", r.data["data"]["reply"].lower())
