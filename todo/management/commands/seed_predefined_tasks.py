from django.core.management.base import BaseCommand
from todo.models import PreDefinedTask


PREDEFINED_TASKS = [
    # Website / App Launch
    {"title": "Register domain name and configure DNS", "category": "website", "priority": "high", "icon": "fas fa-globe", "description": "Purchase domain, configure DNS records, and set up SSL certificate."},
    {"title": "Set up web hosting / cloud server", "category": "website", "priority": "high", "icon": "fas fa-server", "description": "Configure server environment, install dependencies, and deploy application."},
    {"title": "Run cross-browser compatibility test", "category": "website", "priority": "moderate", "icon": "fas fa-browser", "description": "Test application in Chrome, Firefox, Safari, and Edge."},
    {"title": "Perform SEO audit and optimization", "category": "website", "priority": "moderate", "icon": "fas fa-search", "description": "Optimize meta tags, page speed, and structured data."},
    {"title": "Set up analytics (Google Analytics / Mixpanel)", "category": "website", "priority": "moderate", "icon": "fas fa-chart-line", "description": "Install and configure analytics tracking on all key pages."},
    {"title": "Configure error monitoring (Sentry)", "category": "website", "priority": "high", "icon": "fas fa-bug", "description": "Set up real-time error tracking and alerting."},
    {"title": "Write privacy policy and terms of service", "category": "website", "priority": "moderate", "icon": "fas fa-file-contract", "description": "Draft and publish legal documents required for compliance."},
    {"title": "Launch beta testing with 10 users", "category": "website", "priority": "high", "icon": "fas fa-users", "description": "Recruit beta testers, gather feedback, and iterate."},

    # Marketing
    {"title": "Create social media content calendar", "category": "marketing", "priority": "moderate", "icon": "fas fa-calendar-alt", "description": "Plan 30 days of social media posts across all platforms."},
    {"title": "Write and schedule email newsletter", "category": "marketing", "priority": "moderate", "icon": "fas fa-envelope", "description": "Draft newsletter, segment audience, and schedule delivery."},
    {"title": "Set up Google Ads campaign", "category": "marketing", "priority": "high", "icon": "fab fa-google", "description": "Create ad groups, write copy, and set up conversion tracking."},
    {"title": "Produce product demo video", "category": "marketing", "priority": "moderate", "icon": "fas fa-video", "description": "Script, record, and edit a 2-minute product walkthrough video."},
    {"title": "Research and reach out to influencers", "category": "marketing", "priority": "low", "icon": "fas fa-handshake", "description": "Identify relevant influencers and send collaboration proposals."},

    # Design
    {"title": "Create brand style guide", "category": "design", "priority": "high", "icon": "fas fa-paint-brush", "description": "Define typography, colors, logo usage, and visual guidelines."},
    {"title": "Design onboarding flow wireframes", "category": "design", "priority": "high", "icon": "fas fa-pencil-ruler", "description": "Create low-fidelity wireframes for the user onboarding experience."},
    {"title": "Design marketing landing page", "category": "design", "priority": "moderate", "icon": "fas fa-laptop", "description": "Create a high-converting landing page design in Figma."},
    {"title": "Create app icon and favicon", "category": "design", "priority": "moderate", "icon": "fas fa-star", "description": "Design icon in multiple sizes for all platforms."},
    {"title": "Conduct UX audit and usability review", "category": "design", "priority": "moderate", "icon": "fas fa-eye", "description": "Review user flows for friction points and areas of confusion."},

    # Development
    {"title": "Set up CI/CD pipeline", "category": "development", "priority": "high", "icon": "fas fa-code-branch", "description": "Configure automated testing and deployment pipeline."},
    {"title": "Write API documentation", "category": "development", "priority": "moderate", "icon": "fas fa-book", "description": "Document all API endpoints with request/response examples."},
    {"title": "Implement user authentication", "category": "development", "priority": "high", "icon": "fas fa-lock", "description": "Set up login, registration, password reset, and OAuth."},
    {"title": "Set up database backups", "category": "development", "priority": "high", "icon": "fas fa-database", "description": "Configure automated daily backups with offsite storage."},
    {"title": "Write unit and integration tests", "category": "development", "priority": "high", "icon": "fas fa-vial", "description": "Achieve >80% code coverage with automated tests."},
    {"title": "Optimize database queries", "category": "development", "priority": "moderate", "icon": "fas fa-tachometer-alt", "description": "Profile slow queries and add appropriate indexes."},

    # Operations
    {"title": "Create weekly team standup process", "category": "operations", "priority": "moderate", "icon": "fas fa-users", "description": "Define standup format, frequency, and communication tool."},
    {"title": "Document standard operating procedures", "category": "operations", "priority": "moderate", "icon": "fas fa-clipboard-list", "description": "Write SOPs for all key business processes."},
    {"title": "Set up project management workflow", "category": "operations", "priority": "high", "icon": "fas fa-tasks", "description": "Define sprint cadence, backlog grooming, and review process."},
    {"title": "Vendor contract review and renewal", "category": "operations", "priority": "high", "icon": "fas fa-file-signature", "description": "Review all active vendor contracts and negotiate renewals."},

    # Finance
    {"title": "Set up accounting software", "category": "finance", "priority": "high", "icon": "fas fa-calculator", "description": "Configure invoicing, expense tracking, and bank integration."},
    {"title": "Create monthly budget plan", "category": "finance", "priority": "high", "icon": "fas fa-piggy-bank", "description": "Allocate budget across departments and set spending limits."},
    {"title": "File quarterly tax returns", "category": "finance", "priority": "high", "icon": "fas fa-receipt", "description": "Gather financial records and file required tax documents."},

    # HR / Hiring
    {"title": "Write job description for open roles", "category": "hr", "priority": "high", "icon": "fas fa-id-card", "description": "Draft compelling job descriptions for all open positions."},
    {"title": "Set up employee onboarding checklist", "category": "hr", "priority": "moderate", "icon": "fas fa-clipboard-check", "description": "Create a structured first-week onboarding experience for new hires."},
    {"title": "Conduct quarterly performance reviews", "category": "hr", "priority": "moderate", "icon": "fas fa-chart-bar", "description": "Schedule, prepare, and conduct 1:1 performance review sessions."},

    # General
    {"title": "Set up communication channels (Slack/Teams)", "category": "general", "priority": "high", "icon": "fas fa-comments", "description": "Create and configure team channels for effective communication."},
    {"title": "Plan and run project kickoff meeting", "category": "general", "priority": "high", "icon": "fas fa-rocket", "description": "Invite stakeholders, set agenda, and align on project goals."},
    {"title": "Define project milestones and deadlines", "category": "general", "priority": "high", "icon": "fas fa-flag", "description": "Break the project into key milestones with clear due dates."},
    {"title": "Gather stakeholder feedback and requirements", "category": "general", "priority": "high", "icon": "fas fa-comment-dots", "description": "Conduct interviews and workshops to gather all requirements."},
    {"title": "Create project retrospective document", "category": "general", "priority": "low", "icon": "fas fa-history", "description": "Document what went well, what didn't, and action items for next time."},
]


class Command(BaseCommand):
    help = 'Seeds the database with pre-defined task templates'

    def handle(self, *args, **options):
        created_count = 0
        for task_data in PREDEFINED_TASKS:
            obj, created = PreDefinedTask.objects.get_or_create(
                title=task_data['title'],
                category=task_data['category'],
                defaults={
                    'description': task_data.get('description', ''),
                    'suggested_priority': task_data['priority'],
                    'icon': task_data.get('icon', 'fas fa-tasks'),
                }
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} pre-defined tasks '
                f'({PreDefinedTask.objects.count()} total in database)'
            )
        )
