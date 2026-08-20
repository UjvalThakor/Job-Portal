import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from candidates.models import Candidate, Resume
from jobs.models import JobDescription
from jobs.services.analyze import run_analysis

class Command(BaseCommand):
    help = 'Seeds the database with Python and Django developer jobs, candidate profiles, and runs AI analysis.'

    def handle(self, *args, **options):
        self.stdout.write("Adding specialized Python & Django Developer jobs...")

        python_django_jobs = [
            {
                "title": "Junior Python / Django Developer",
                "department": "Engineering",
                "min_experience_years": 1.0,
                "required_skills": ["Python", "Django", "HTML", "CSS", "Git", "SQL"],
                "preferred_skills": ["Django REST Framework", "Bootstrap", "PostgreSQL"],
                "description": "Ideal entry-level position for a Junior Developer building core Django web views, templates, and database models."
            },
            {
                "title": "Mid-Level Django Backend Engineer",
                "department": "Engineering",
                "min_experience_years": 3.0,
                "required_skills": ["Python", "Django", "Django REST Framework", "PostgreSQL", "Redis"],
                "preferred_skills": ["Celery", "Docker", "Unit Testing", "Swagger/OpenAPI"],
                "description": "Designing relational database schemas, RESTful API endpoints, caching strategies, and background job processing."
            },
            {
                "title": "Lead Python / Django Architect",
                "department": "Engineering",
                "min_experience_years": 7.0,
                "required_skills": ["Python", "Django", "System Architecture", "PostgreSQL", "AWS", "Docker", "Security"],
                "preferred_skills": ["Kubernetes", "Microservices", "CI/CD", "Redis", "Celery"],
                "description": "Architecting enterprise-scale Django applications, high-availability database replication, and technical leadership."
            },
            {
                "title": "Django & React Full Stack Engineer",
                "department": "Engineering",
                "min_experience_years": 3.0,
                "required_skills": ["Python", "Django", "React", "JavaScript", "TypeScript", "REST API"],
                "preferred_skills": ["Redux", "TailwindCSS", "PostgreSQL", "Docker"],
                "description": "Building full-stack web platforms connecting Django REST backends with modern React & TypeScript frontends."
            },
            {
                "title": "Django & FastAPI Microservices Developer",
                "department": "Engineering",
                "min_experience_years": 3.0,
                "required_skills": ["Python", "Django", "FastAPI", "Asyncio", "Docker", "PostgreSQL"],
                "preferred_skills": ["gRPC", "Redis", "Kafka", "RabbitMQ"],
                "description": "Developing asynchronous microservices using FastAPI alongside monolithic Django administration backends."
            },
            {
                "title": "Python & Django Automation Engineer",
                "department": "Engineering",
                "min_experience_years": 2.0,
                "required_skills": ["Python", "Django", "Celery", "Selenium", "Web Scraping", "REST API"],
                "preferred_skills": ["BeautifulSoup", "Redis", "PostgreSQL"],
                "description": "Creating automated task pipelines, data extraction workflows, and asynchronous batch processing with Celery."
            },
            {
                "title": "Python AI Integration & Django Engineer",
                "department": "Engineering",
                "min_experience_years": 3.0,
                "required_skills": ["Python", "Django", "REST API", "OpenAI API", "LangChain", "Vector Databases"],
                "preferred_skills": ["PyTorch", "FastAPI", "PostgreSQL", "Docker"],
                "description": "Integrating LLMs, generative AI features, and vector search indexing directly into Django backend applications."
            },
            {
                "title": "NodeJS Developer",
                "department": "Engineering",
                "min_experience_years": 2.0,
                "required_skills": ["Node.js", "Express.js", "JavaScript", "MongoDB", "REST API"],
                "preferred_skills": ["TypeScript", "Docker", "AWS", "GraphQL"],
                "description": "Building high-speed asynchronous backend APIs, microservices, and web sockets using Node.js and Express."
            },
            {
                "title": "E-Commerce Product Listing Specialist",
                "department": "E-Commerce Operations",
                "min_experience_years": 1.0,
                "required_skills": ["E-Commerce", "Product Catalog", "SEO", "Inventory Management", "MS Excel"],
                "preferred_skills": ["Shopify", "Amazon Seller Central", "Digital Marketing"],
                "description": "Managing online product catalogs, listing optimizations, inventory syncing, and order processing across platforms."
            },
            {
                "title": "Senior Travel Consultant",
                "department": "Hospitality & Travel",
                "min_experience_years": 4.0,
                "required_skills": ["Travel Itinerary", "GDS System", "Customer Service", "Ticketing", "Vendor Relations"],
                "preferred_skills": ["Corporate Travel", "International Packages", "Destination Management"],
                "description": "Designing customized travel itineraries, ticketing reservations, corporate travel management, and client support."
            },
            {
                "title": "Frontend React & TypeScript Engineer",
                "department": "Engineering",
                "min_experience_years": 3.0,
                "required_skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Redux Toolkit"],
                "preferred_skills": ["Next.js", "TailwindCSS", "Jest", "Webpack"],
                "description": "Crafting responsive, high-performance web user interfaces, interactive component design systems, and API state hooks."
            }
        ]

        created_jobs = []
        for jdata in python_django_jobs:
            job, created = JobDescription.objects.get_or_create(
                title=jdata["title"],
                defaults=jdata
            )
            created_jobs.append(job)

        self.stdout.write(f"Added {len(created_jobs)} specialized Python & Django developer jobs.")

        # Sample Candidates
        sample_candidates_data = [
            {
                "full_name": "Aarav Mehta",
                "email": "aarav.mehta@example.com",
                "phone": "+91 98765 43210",
                "address": "Bengaluru, Karnataka, India",
                "skills": ["Python", "Django", "Django REST Framework", "PostgreSQL", "Redis", "Docker", "Git", "SQL"],
                "total_experience_years": 3.5,
                "education": [{"degree": "B.Tech in Computer Science", "institution": "NIT Karnataka", "year": "2021"}],
                "experience": [{"title": "Software Engineer", "company": "TechCorp India", "duration": "2021 - Present"}],
                "projects": ["Scalable Django E-Commerce Backend with Redis Cache", "Automated Resume Parser with Python NLP"],
                "certifications": ["AWS Certified Developer Associate"],
                "languages": ["English", "Hindi"]
            },
            {
                "full_name": "Sophia Williams",
                "email": "sophia.w@example.com",
                "phone": "+1 (555) 234-5678",
                "address": "San Francisco, CA, USA",
                "skills": ["Python", "Django", "System Architecture", "PostgreSQL", "AWS", "Docker", "Security", "Kubernetes", "Microservices"],
                "total_experience_years": 7.5,
                "education": [{"degree": "M.S. in Software Engineering", "institution": "Stanford University", "year": "2017"}],
                "experience": [{"title": "Senior Staff Architect", "company": "CloudScale Inc", "duration": "2018 - Present"}],
                "projects": ["Distributed Multi-tenant Django Platform handling 20M requests/day"],
                "certifications": ["AWS Solutions Architect Professional", "Certified Kubernetes Administrator"],
                "languages": ["English"]
            },
            {
                "full_name": "Priya Sharma",
                "email": "priya.sharma@example.com",
                "phone": "+91 91234 56789",
                "address": "Surat, Gujarat, India",
                "skills": ["Python", "Django", "HTML", "CSS", "JavaScript", "SQL", "Git", "Bootstrap"],
                "total_experience_years": 1.2,
                "education": [{"degree": "B.E. in Information Technology", "institution": "GTU Ahmedabad", "year": "2023"}],
                "experience": [{"title": "Junior Web Developer", "company": "InnoSoft Solutions", "duration": "2023 - Present"}],
                "projects": ["Employee Attendance & HR Management Portal with Django"],
                "certifications": ["Python Institute PCAP Certification"],
                "languages": ["English", "Hindi", "Gujarati"]
            },
            {
                "full_name": "David Chen",
                "email": "david.chen@example.com",
                "phone": "+1 (555) 876-5432",
                "address": "Austin, TX, USA",
                "skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Redux Toolkit", "Next.js", "TailwindCSS"],
                "total_experience_years": 4.0,
                "education": [{"degree": "B.S. in Computer Science", "institution": "UT Austin", "year": "2020"}],
                "experience": [{"title": "Senior Frontend Developer", "company": "PixelCraft Studio", "duration": "2020 - Present"}],
                "projects": ["Next.js Enterprise SaaS Analytics Dashboard", "Design System UI Kit with Tailwind"],
                "certifications": ["Meta Certified Frontend Developer"],
                "languages": ["English", "Mandarin"]
            }
        ]

        for cdata in sample_candidates_data:
            candidate, created = Candidate.objects.get_or_create(
                email=cdata["email"],
                defaults=cdata
            )

        # Re-run candidate analysis for all jobs
        candidates = Candidate.objects.all()
        eval_count = 0
        for candidate in candidates:
            resume = candidate.resumes.first()
            for job in created_jobs:
                run_analysis(candidate, job, resume)
                eval_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully evaluated candidates against new Python & Django jobs ({eval_count} evaluations)! Total jobs: {JobDescription.objects.count()}, Candidates: {Candidate.objects.count()}"))

