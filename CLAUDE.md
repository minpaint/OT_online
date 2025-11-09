# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Guidelines

**ВАЖНО:** Всегда отвечай на русском языке при работе с этим проектом. Это российско-белорусская система управления охраной труда, и все коммуникации должны быть на русском языке, чтобы соответствовать контексту проекта и ожиданиям пользователя.

**IMPORTANT:** Always respond in Russian when working with this project. This is a Russian-Belarusian occupational safety management system, and all communications should be in Russian to match the project context and user expectations.

## Project Overview

**OT_online** is a comprehensive occupational safety management system (охрана труда) built with Django 5.0. It manages organizational structure, employees, equipment, personal protective equipment (PPE/СИЗ), medical examinations, commissions, and safety quizzes for Russian/Belarusian organizations.

**Primary Language:** Russian (with Belarusian support)
**Python Environment:** Windows, uses virtual environment at `c:\venvs\OT_online\Scripts\python.exe`

## Common Commands

### Development

```bash
# Run development server
py manage.py runserver

# Run development server on alternative port with exam subdomain support
py manage.py runserver 8001

# Create migrations
py manage.py makemigrations

# Apply migrations
py manage.py migrate

# Check for issues
py manage.py check

# Django shell
py manage.py shell

# Create superuser
py manage.py createsuperuser

# Collect static files (for production)
py manage.py collectstatic
```

### Database Operations

```bash
# Show specific migration SQL
py manage.py sqlmigrate directory 0025

# List migrations
py manage.py showmigrations

# Rollback migration
py manage.py migrate directory 0024
```

### Custom Management Commands

```bash
# Import quiz questions (v1)
py manage.py import_quiz_questions

# Import quiz questions (v2, improved)
py manage.py import_quiz_questions_v2
```

## Architecture Overview

### Single-App Structure

The project uses a monolithic Django app structure with **one main application** called `directory` that contains all functionality. This differs from typical multi-app Django projects.

```
OT_online/
├── directory/              # Main and only Django app
│   ├── models/            # Models split by domain (17 models)
│   ├── admin/             # Admin classes split by domain
│   ├── views/             # Views split by functional area
│   ├── resources/         # django-import-export resources
│   ├── forms/             # Form classes
│   ├── middleware/        # Custom middleware
│   └── management/        # Custom management commands
├── templates/             # Global templates
├── static/                # Global static files
├── media/                 # User-uploaded files
├── config/                # Django admin configuration
├── settings.py            # Main settings file
├── settings_prod.py       # Production settings
├── urls.py                # Root URL configuration
└── manage.py              # Django management script
```

### Key Architectural Patterns

1. **Model Organization:** Models are split into separate files by domain (e.g., `employee.py`, `quiz.py`, `medical_examination.py`) but all imported in `directory/models/__init__.py`

2. **Admin Organization:** Each model has its own admin file in `directory/admin/` with custom admin classes, often using `django-import-export` and `nested-admin`

3. **URL Namespacing:** Uses nested URL namespacing:
   - Root: `directory` namespace
   - Sub-namespaces: `auth`, `employees`, `positions`, `quiz`, `medical`, etc.
   - Example: `reverse('directory:quiz:quiz_start', args=[quiz_id])`

4. **Tree View Pattern:** Custom tree-based admin views for hierarchical data (Organization → Subdivision → Department) used for Position, Employee, and Equipment models

5. **Exam Subdomain Isolation:** The quiz system uses a separate subdomain (`exam.*`) with strict access control via middleware (`ExamSubdomainMiddleware`)

### Domain Models (17 Total)

**Organizational Structure (4 models):**
- `Organization` - Companies/organizations
- `StructuralSubdivision` - Departments/divisions
- `Department` - Sub-departments
- `Profile` - User profiles with multi-organization access

**Personnel (3 models):**
- `Position` - Job positions with safety requirements
- `Employee` - Staff members
- `EmployeeHiring` - Hiring history

**Equipment & Documents (2 models):**
- `Equipment` - Equipment requiring maintenance
- `Document` - General documents

**PPE/СИЗ System (3 models):**
- `SIZ` - PPE catalog
- `SIZNorm` - PPE issuance standards per position
- `SIZIssued` - Issued PPE tracking

**Medical Examinations (5 models):**
- `MedicalExaminationType` - Exam types
- `HarmfulFactor` - Occupational hazards
- `MedicalExaminationNorm` - Reference norms
- `PositionMedicalFactor` - Position-hazard mapping
- `EmployeeMedicalExamination` - Employee exam records

**Commissions & Documents (4 models):**
- `Commission` - Safety commissions
- `CommissionMember` - Commission participants
- `DocumentTemplate` - DOCX templates
- `GeneratedDocument` - Generated documents

**Quiz System (6 models):**
- `QuizCategory` - Quiz categories/topics
- `Quiz` - Quiz definitions (training or exam mode)
- `Question` - Questions with images
- `Answer` - Answer options
- `QuizAttempt` - User attempts
- `UserAnswer` - Individual answers
- `QuizAccessToken` - Token-based access
- `QuizQuestionOrder` - Question ordering

## Critical Implementation Details

### 1. Hierarchical Validation

Many models enforce organizational hierarchy validation in their `clean()` method:
- Department must belong to the same organization as its subdivision
- Employee's position must be in the same organizational unit
- Equipment must belong to valid org structure

**When modifying these models**, always maintain validation logic.

### 2. Quiz System Subdomain Security

The quiz system operates on `exam.*` subdomain with strict isolation:

- **Middleware:** `ExamSubdomainMiddleware` blocks ALL non-quiz URLs on exam subdomain
- **Access Control:** Only accessible via `QuizAccessToken` stored in session
- **No Indexing:** robots.txt and X-Robots-Tag headers prevent search engine indexing
- **Security Headers:** CSP, Cache-Control, X-Frame-Options enforce strict security

**When working with quiz views:**
- Check for `request.session.get('quiz_token_mode')` for token-based access
- Use `@login_required` for regular authenticated access
- Store quiz question order in session: `request.session[f'quiz_questions_{attempt_id}']`

### 3. Import/Export System

Uses `django-import-export` with custom Resource classes:
- **StructureResource** - Cascading import: Organization → Subdivision → Department
- **EmployeeResource** - Auto-generates dative case (дательный падеж) using `pymorphy2`
- **EquipmentResource** - Auto-generates inventory numbers (8 digits)

Import process stores preview data in session for confirmation step.

### 4. Document Generation

System supports DOCX template-based document generation using `docxtpl`:
- Templates stored in `media/document_templates/`
- Generated documents in `media/generated_documents/YYYY/MM/DD/`
- Templates can be "reference" (is_default=True) or organization-specific

**Context data** is stored in JSON format in `GeneratedDocument.document_data`.

### 5. Maintenance Date Calculations

Equipment maintenance uses custom date arithmetic in `Equipment._add_months()` that handles month-end edge cases correctly. Always use this method for maintenance date calculations, not simple `timedelta`.

### 6. Declension System

Russian declension using `pymorphy2` for:
- Employee names (nominative → dative for orders/documents)
- Position names in generated documents

Found in `directory/utils/declension.py`.

## Settings and Configuration

### Environment Variables

Configuration loaded from `.env` file (use `python-dotenv`):

**Critical variables:**
- `DJANGO_SECRET_KEY` - Secret key for Django
- `DJANGO_DEBUG` - Debug mode (True/False)
- `DJANGO_ALLOWED_HOSTS` - Comma-separated host list
- `DATABASE_URL` or `DB_ENGINE`, `DB_NAME`, etc. - Database config
- `EXAM_SUBDOMAIN` - Exam subdomain (default: exam.localhost:8001)
- `EXAM_PROTOCOL` - Protocol for exam subdomain (http/https)

**Defaults to SQLite** if no database variables set.

### Two Settings Files

- `settings.py` - Development/staging settings
- `settings_prod.py` - Production settings

### Static Files

- **Development:** Served by Django from `STATICFILES_DIRS`
- **Production:** Uses WhiteNoise with `CompressedManifestStaticFilesStorage`
- **Collection path:** `../data/static/` (outside project root for hosting)

### Media Files

- **Path:** `BASE_DIR / 'media'`
- **Subdirectories:**
  - `quiz/questions/` - Quiz question images
  - `document_templates/` - DOCX templates
  - `generated_documents/` - Generated documents
  - `medical/certificates/` - Medical certificates

## Testing Considerations

When writing tests:

1. **Use `TESTING` flag:** Settings detect test mode via `sys.argv[1] == 'test'`
2. **Separate test DB:** SQLite uses `test_db.sqlite3` for tests
3. **Debug toolbar disabled** during tests
4. **Session handling:** Quiz system heavily uses session - mock appropriately

## Database Migrations

**Migration naming convention:** Use descriptive names with `--name` flag:
```bash
py manage.py makemigrations directory --name add_quiz_access_tokens
```

**Recent major migrations:**
- `0025_add_quiz_models` - Added entire quiz system
- `0029_*_quizaccesstoken` - Added token-based access
- `0034_remove_quiz_type` - Removed deprecated quiz_type field

## Common Patterns

### Autocomplete Views

Uses `django-autocomplete-light` (DAL) with Select2:
- All autocomplete views in `directory/autocomplete_views.py`
- URL pattern: `/directory/autocomplete/{model}/`
- Forward fields supported for cascading dropdowns

### Admin Tree Views

Custom template with JavaScript for collapsible tree:
- Template: `templates/admin/directory/{model}/change_list_tree.html`
- JavaScript: `static/admin/js/tree_view.js`
- Used for: Position, Employee, Equipment

### Validation Pattern

Models use `clean()` method for validation:
```python
def clean(self):
    if self.department and self.department.organization != self.organization:
        raise ValidationError("Department must belong to same organization")
```

Always call `super().clean()` and validate hierarchical relationships.

### Russian Date/Number Formatting

Use `DATE_FORMAT`, `DATETIME_FORMAT` settings for Russian format:
- Language: `ru-ru`
- Timezone: `Europe/Moscow`
- USE_TZ = True (use timezone-aware datetimes)

## Important Quirks

1. **inspect.getargspec monkeypatch:** Required in `manage.py` for Python 3.11+ compatibility with `pymorphy2`

2. **Organization field everywhere:** Almost all models have `organization` ForeignKey - this is intentional for multi-tenancy

3. **Russian field names:** Model fields often use transliterated Russian (e.g., `full_name_nominative`, `full_name_dative`)

4. **Emoji in admin:** Admin interface uses emoji extensively for visual clarity (🏢, 👥, 📋, etc.)

5. **Custom middleware order:** `ExamSubdomainMiddleware` must be early in middleware stack to enforce subdomain restrictions

6. **No REST API:** System uses traditional Django views with AJAX endpoints for interactivity (not Django REST Framework)

## Documentation Files

- `docs/PROJECT_DESCRIPTION.md` - Comprehensive project documentation
- `docs/QUIZ_SYSTEM.md` - Quiz system architecture and usage
- `docs/QUIZ_TOKEN_SETUP.md` - Token-based access setup
- `docs/QUIZ_IMPORT_GUIDE.md` - Importing quiz questions
- `docs/SECURITY_GUIDE.md` - Security best practices
- `docs/IMPORT_EXPORT.md` - Import/export functionality

## Production Deployment Notes

- Use `settings_prod.py` for production
- Configure `STATIC_ROOT` to `../data/static/`
- Set `SECURE_SSL_REDIRECT`, `HSTS` headers for HTTPS
- Configure proper `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- Use PostgreSQL (configured via `DATABASE_URL`)
- Set up WhiteNoise for static file serving
- Configure exam subdomain in DNS and web server

## Known Issues and Workarounds

1. **pymorphy2 on Python 3.11+:** Requires `inspect.getargspec` monkeypatch in `manage.py`
2. **Windows paths:** Project developed on Windows - path handling uses `Path` objects for cross-platform compatibility
3. **Exam subdomain on localhost:** Use `exam.localhost:8001` format, ensure proper hosts file or browser support
