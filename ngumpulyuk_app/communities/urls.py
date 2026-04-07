from django.urls import path

from ngumpulyuk_app.communities import views

urlpatterns = [
    path("communities/", views.CommunityListCreateView.as_view(), name="communities-list"),
    path("communities/<uuid:id>/", views.CommunityDetailView.as_view(), name="communities-detail"),
    path("communities/<uuid:id>/join/", views.CommunityJoinView.as_view(), name="communities-join"),
    path("communities/<uuid:id>/leave/", views.CommunityLeaveView.as_view(), name="communities-leave"),
    path("communities/<uuid:id>/members/", views.CommunityMembersView.as_view(), name="communities-members"),
    path("communities/<uuid:id>/members/<uuid:user_id>/role/", views.CommunityMemberRoleView.as_view(), name="community-member-role"),
    path("communities/<uuid:id>/threads/", views.CommunityThreadsView.as_view(), name="community-threads"),
]
