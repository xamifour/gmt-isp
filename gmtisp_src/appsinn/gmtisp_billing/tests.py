# tests.py

from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from openwisp_users.models import Organization
from .models import Plan, UserPlan
from .admin import PlanAdmin, UserPlanAdmin
from openwisp_utils.utils import get_db_for_organization

User = get_user_model()

class MockRequest:
    def __init__(self, user):
        self.user = user

class OrganizationAdminTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        
        # Create an organization and users
        self.org1 = Organization.objects.create(name='GIES', slug='gies')
        self.org2 = Organization.objects.create(name='GIGMEG', slug='gigmeg')
        
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password')
        self.user1.organization = self.org1
        self.user1.save()
        
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        self.user2.organization = self.org2
        self.user2.save()
        
        self.plan_admin = PlanAdmin(Plan, self.site)
        self.user_plan_admin = UserPlanAdmin(UserPlan, self.site)

    def test_create_plan(self):
        request = MockRequest(self.user1)
        plan = Plan(name='Test Plan', organization=self.org1)
        self.plan_admin.save_model(request, plan, form=None, change=False)
        
        self.assertEqual(
            Plan.objects.using(get_db_for_organization(self.org1)).count(), 1
        )

    def test_update_plan(self):
        request = MockRequest(self.user1)
        plan = Plan.objects.using(get_db_for_organization(self.org1)).create(
            name='Test Plan', organization=self.org1
        )
        plan.name = 'Updated Plan'
        self.plan_admin.save_model(request, plan, form=None, change=True)
        
        updated_plan = Plan.objects.using(get_db_for_organization(self.org1)).get(pk=plan.pk)
        self.assertEqual(updated_plan.name, 'Updated Plan')

    def test_delete_plan(self):
        request = MockRequest(self.user1)
        plan = Plan.objects.using(get_db_for_organization(self.org1)).create(
            name='Test Plan', organization=self.org1
        )
        self.plan_admin.delete_model(request, plan)
        
        self.assertEqual(
            Plan.objects.using(get_db_for_organization(self.org1)).count(), 0
        )

    def test_create_user_plan(self):
        request = MockRequest(self.user1)
        user_plan = UserPlan(user=self.user1, plan=Plan.objects.using(get_db_for_organization(self.org1)).create(
            name='Test Plan', organization=self.org1))
        self.user_plan_admin.save_model(request, user_plan, form=None, change=False)
        
        self.assertEqual(
            UserPlan.objects.using(get_db_for_organization(self.org1)).count(), 1
        )
