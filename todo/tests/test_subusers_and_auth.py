"""
Tests for Sub-Users / Team Hierarchy, Quotas (Max 99), Project Invites,
and Strict Authentication Enforcement.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from todo.models import Task, Category, UserProfile
from todo.services import SubUserService, CategoryService, TaskService


class StrictAuthEnforcementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='mainowner', password='Password123!', email='owner@example.com')

    def test_unauthenticated_access_to_dashboard_redirects_to_login(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_unauthenticated_access_to_kanban_redirects_to_login(self):
        resp = self.client.get(reverse('manage_kanban'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_unauthenticated_access_to_projects_redirects_to_login(self):
        resp = self.client.get(reverse('manage_projects'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_unauthenticated_access_to_team_redirects_to_login(self):
        resp = self.client.get(reverse('manage_team'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_authenticated_user_accesses_dashboard_with_recent_projects(self):
        self.client.login(username='mainowner', password='Password123!')
        cat = Category.objects.create(user=self.user, name='Alpha Project', color='#3b82f6')
        Task.objects.create(user=self.user, title='Test Task 1', category=cat, status=Task.Status.TO_DO)

        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('recent_projects', resp.context)
        self.assertIn('subusers', resp.context)
        self.assertTrue(resp.context['is_owner'])
        self.assertEqual(resp.context['max_subusers'], 99)
        self.assertContains(resp, 'Alpha Project')
        self.assertContains(resp, 'Recent Projects')


class SubUserManagementServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='firm_admin', password='Password123!')
        self.project1 = Category.objects.create(user=self.owner, name='Backend API', color='#3b82f6')
        self.project2 = Category.objects.create(user=self.owner, name='Mobile App', color='#10b981')

    def test_create_subuser_without_unique_email_success(self):
        subuser = SubUserService.create_subuser(
            owner=self.owner,
            username='dev_john',
            password='secretpassword1',
            display_name='John Doe',
            role='member',
            assigned_project_ids=[self.project1.id]
        )
        self.assertEqual(subuser.username, 'dev_john')
        self.assertEqual(subuser.first_name, 'John Doe')
        self.assertTrue(subuser.profile.is_subuser)
        self.assertEqual(subuser.profile.parent_user, self.owner)
        self.assertEqual(subuser.profile.role, 'member')
        self.assertIn(self.project1, subuser.shared_categories.all())
        self.assertNotIn(self.project2, subuser.shared_categories.all())

    def test_subuser_can_login_with_assigned_credentials(self):
        SubUserService.create_subuser(
            owner=self.owner,
            username='dev_sarah',
            password='SarahPassword99!',
            display_name='Sarah Connor'
        )
        client = Client()
        login_success = client.login(username='dev_sarah', password='SarahPassword99!')
        self.assertTrue(login_success)

    def test_subuser_sees_assigned_projects(self):
        subuser = SubUserService.create_subuser(
            owner=self.owner,
            username='dev_alex',
            password='password123',
            assigned_project_ids=[self.project2.id]
        )
        cats = CategoryService.get_categories(subuser)
        self.assertEqual(cats.count(), 1)
        self.assertEqual(cats.first().name, 'Mobile App')

    def test_update_subuser_username_and_password(self):
        subuser = SubUserService.create_subuser(
            owner=self.owner,
            username='old_name',
            password='password123',
            display_name='Old Name'
        )
        updated = SubUserService.update_subuser(
            owner=self.owner,
            subuser_id=subuser.id,
            username='new_name',
            password='newpassword456',
            display_name='New Name',
            role='admin',
            assigned_project_ids=[self.project1.id, self.project2.id]
        )
        self.assertEqual(updated.username, 'new_name')
        self.assertEqual(updated.first_name, 'New Name')
        self.assertEqual(updated.profile.role, 'admin')
        self.assertTrue(updated.check_password('newpassword456'))
        self.assertEqual(updated.shared_categories.count(), 2)

    def test_delete_subuser(self):
        subuser = SubUserService.create_subuser(
            owner=self.owner,
            username='to_delete',
            password='password123',
            assigned_project_ids=[self.project1.id]
        )
        res = SubUserService.delete_subuser(self.owner, subuser.id)
        self.assertTrue(res)
        self.assertFalse(User.objects.filter(username='to_delete').exists())

    def test_subuser_cannot_create_other_subusers(self):
        subuser = SubUserService.create_subuser(
            owner=self.owner,
            username='sub_member',
            password='password123'
        )
        with self.assertRaises(ValueError):
            SubUserService.create_subuser(
                owner=subuser,
                username='sub_nested',
                password='password123'
            )

    def test_max_99_subusers_limit_enforced(self):
        # Create 99 subusers quickly with bulk_create
        users = [User(username=f'bulk_sub_{i}', email=f'bulk_{i}@local') for i in range(99)]
        User.objects.bulk_create(users)
        created_users = list(User.objects.filter(username__startswith='bulk_sub_'))
        profiles = [
            UserProfile(user=u, is_subuser=True, parent_user=self.owner, role='member')
            for u in created_users
        ]
        UserProfile.objects.bulk_create(profiles)

        self.assertEqual(SubUserService.get_subusers(self.owner).count(), 99)

        # Attempting 100th subuser should raise ValueError
        with self.assertRaises(ValueError) as ctx:
            SubUserService.create_subuser(
                owner=self.owner,
                username='overflow_user',
                password='password123'
            )
        self.assertIn('Maximum 99 sub-users allowed', str(ctx.exception))


class SubUserAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='api_owner', password='Password123!')
        self.project = Category.objects.create(user=self.owner, name='Test Project', color='#ef4444')
        self.client.login(username='api_owner', password='Password123!')

    def test_api_subuser_create(self):
        resp = self.client.post(
            reverse('api_subuser_create'),
            data={
                'username': 'new_worker',
                'password': 'workerpassword123',
                'display_name': 'Worker One',
                'role': 'member',
                'assigned_projects': [self.project.id]
            },
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['subuser']['username'], 'new_worker')

        created = User.objects.get(username='new_worker')
        self.assertTrue(created.profile.is_subuser)
        self.assertEqual(created.profile.parent_user, self.owner)

    def test_api_subuser_list(self):
        SubUserService.create_subuser(self.owner, 'list_user1', 'pass1234')
        resp = self.client.get(reverse('api_subusers_list'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['max_subusers'], 99)

    def test_api_subuser_update(self):
        sub = SubUserService.create_subuser(self.owner, 'update_me', 'pass1234')
        resp = self.client.post(
            reverse('api_subuser_update', kwargs={'pk': sub.id}),
            data={'display_name': 'Updated Name', 'role': 'admin'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        sub.refresh_from_db()
        self.assertEqual(sub.first_name, 'Updated Name')
        self.assertEqual(sub.profile.role, 'admin')

    def test_api_subuser_delete(self):
        sub = SubUserService.create_subuser(self.owner, 'delete_me_api', 'pass1234')
        resp = self.client.post(
            reverse('api_subuser_delete', kwargs={'pk': sub.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='delete_me_api').exists())


class ProjectInviteFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='proj_owner', password='Password123!')
        self.member = User.objects.create_user(username='proj_member', password='Password123!')
        self.project = Category.objects.create(user=self.owner, name='Collab Hub', color='#8b5cf6')

    def test_project_invite_link_join(self):
        token = self.project.ensure_share_token()
        self.client.login(username='proj_member', password='Password123!')
        resp = self.client.get(reverse('project_join', kwargs={'token': token}), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.member, self.project.members.all())
