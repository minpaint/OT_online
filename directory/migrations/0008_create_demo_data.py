from django.db import migrations
from django.utils import timezone
from datetime import datetime, timedelta


def create_demo_data(apps, schema_editor):
    """
    Создание демонстрационных данных для всех основных моделей.
    """
    # Получаем модели из приложения
    Organization = apps.get_model('directory', 'Organization')
    StructuralSubdivision = apps.get_model('directory', 'StructuralSubdivision')
    Department = apps.get_model('directory', 'Department')
    Position = apps.get_model('directory', 'Position')
    Employee = apps.get_model('directory', 'Employee')
    Document = apps.get_model('directory', 'Document')
    Equipment = apps.get_model('directory', 'Equipment')

    # Даты для использования в записях
    today = datetime.now().date()
    birth_date_base = today - timedelta(days=365 * 40)  # примерно 40 лет назад

    # ========== 1. СОЗДАЕМ ОРГАНИЗАЦИИ ==========

    org1 = Organization.objects.create(
        full_name_ru="Общество с ограниченной ответственностью 'ТехноИнновации'",
        short_name_ru="ООО 'ТехноИнновации'",
        full_name_by="Таварыства з абмежаванай адказнасцю 'ТэхнаIнавацыi'",
        short_name_by="ТАА 'ТэхнаIнавацыi'",
        requisites_ru="ИНН: 7712345678, КПП: 771201001, ОГРН: 1027700123456\nАдрес: г. Москва, ул. Технологическая, д. 42",
        requisites_by="УНП: 191123456, Юр. адрас: г. Мiнск, вул. Тэхналагiчная, д. 42"
    )

    org2 = Organization.objects.create(
        full_name_ru="Акционерное общество 'МедикалГруп'",
        short_name_ru="АО 'МедикалГруп'",
        full_name_by="Акцыянернае таварыства 'МедыкалГруп'",
        short_name_by="АТ 'МедыкалГруп'",
        requisites_ru="ИНН: 7709876543, КПП: 770901001, ОГРН: 1027700654321\nАдрес: г. Москва, ул. Здоровья, д. 15",
        requisites_by="УНП: 191654321, Юр. адрас: г. Мiнск, вул. Здароўя, д. 15"
    )

    org3 = Organization.objects.create(
        full_name_ru="Закрытое акционерное общество 'СтройКомплекс'",
        short_name_ru="ЗАО 'СтройКомплекс'",
        full_name_by="Закрытае акцыянернае таварыства 'БудКомплекс'",
        short_name_by="ЗАТ 'БудКомплекс'",
        requisites_ru="ИНН: 5038123456, КПП: 503801001, ОГРН: 1035007556677\nАдрес: Московская обл., г. Пушкино, ул. Строителей, д. 7",
        requisites_by="УНП: 192556677, Юр. адрас: Мiнская вобл., г. Дзяржынск, вул. Будаўнiкоў, д. 7"
    )

    # ========== 2. СОЗДАЕМ СТРУКТУРНЫЕ ПОДРАЗДЕЛЕНИЯ ==========

    # Подразделения для ООО "ТехноИнновации"
    sub_it_1 = StructuralSubdivision.objects.create(
        name="IT-департамент",
        short_name="IT-деп",
        organization=org1
    )

    sub_finance_1 = StructuralSubdivision.objects.create(
        name="Финансовый департамент",
        short_name="Фин-деп",
        organization=org1
    )

    sub_hr_1 = StructuralSubdivision.objects.create(
        name="HR-департамент",
        short_name="HR-деп",
        organization=org1
    )

    # Подразделения для АО "МедикалГруп"
    sub_clinic = StructuralSubdivision.objects.create(
        name="Клиническое отделение",
        short_name="Клин-отд",
        organization=org2
    )

    sub_research = StructuralSubdivision.objects.create(
        name="Научно-исследовательский центр",
        short_name="НИЦ",
        organization=org2
    )

    # Подразделения для ЗАО "СтройКомплекс"
    sub_construction = StructuralSubdivision.objects.create(
        name="Строительный департамент",
        short_name="Строй-деп",
        organization=org3
    )

    sub_design = StructuralSubdivision.objects.create(
        name="Проектный департамент",
        short_name="Проект-деп",
        organization=org3
    )

    # ========== 3. СОЗДАЕМ ОТДЕЛЫ ==========

    # Отделы для IT-департамента ООО "ТехноИнновации"
    dept_dev = Department.objects.create(
        name="Отдел разработки",
        short_name="Разработка",
        organization=org1,
        subdivision=sub_it_1
    )

    dept_qa = Department.objects.create(
        name="Отдел тестирования",
        short_name="QA",
        organization=org1,
        subdivision=sub_it_1
    )

    dept_infra = Department.objects.create(
        name="Отдел инфраструктуры",
        short_name="Инфраструктура",
        organization=org1,
        subdivision=sub_it_1
    )

    # Отделы для Финансового департамента ООО "ТехноИнновации"
    dept_accounting = Department.objects.create(
        name="Бухгалтерия",
        short_name="Бух",
        organization=org1,
        subdivision=sub_finance_1
    )

    # Отделы для HR-департамента
    dept_hr = Department.objects.create(
        name="Отдел кадров",
        short_name="Кадры",
        organization=org1,
        subdivision=sub_hr_1
    )

    # Отделы для Клинического отделения АО "МедикалГруп"
    dept_therapy = Department.objects.create(
        name="Терапевтическое отделение",
        short_name="Терапия",
        organization=org2,
        subdivision=sub_clinic
    )

    dept_surgery = Department.objects.create(
        name="Хирургическое отделение",
        short_name="Хирургия",
        organization=org2,
        subdivision=sub_clinic
    )

    # Отделы для НИЦ АО "МедикалГруп"
    dept_research = Department.objects.create(
        name="Лаборатория исследований",
        short_name="Лаборатория",
        organization=org2,
        subdivision=sub_research
    )

    # Отделы для Строительного департамента ЗАО "СтройКомплекс"
    dept_construction = Department.objects.create(
        name="Отдел строительства",
        short_name="Строители",
        organization=org3,
        subdivision=sub_construction
    )

    # Отделы для Проектного департамента ЗАО "СтройКомплекс"
    dept_design = Department.objects.create(
        name="Отдел проектирования",
        short_name="Проектировщики",
        organization=org3,
        subdivision=sub_design
    )

    # ========== 4. СОЗДАЕМ ДОЛЖНОСТИ ==========

    # --- Должности в ООО "ТехноИнновации" ---

    # Уровень организации
    pos_ceo_1 = Position.objects.create(
        position_name="Генеральный директор",
        organization=org1,
        is_responsible_for_safety=True,
        commission_role='chairman',
        safety_instructions_numbers="ОТ-01, ОТ-02, ПБ-01",
        electrical_safety_group="V",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    # IT-департамент
    pos_it_director = Position.objects.create(
        position_name="Директор IT-департамента",
        organization=org1,
        subdivision=sub_it_1,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, ОТ-03, ИТ-01",
        electrical_safety_group="IV",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    # Отдел разработки
    pos_dev_lead = Position.objects.create(
        position_name="Руководитель отдела разработки",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_dev,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, ИТ-01, ИТ-02",
        electrical_safety_group="III",
        can_be_internship_leader=True,
        internship_period_days=14
    )

    pos_senior_dev = Position.objects.create(
        position_name="Старший разработчик",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_dev,
        safety_instructions_numbers="ОТ-01, ИТ-01, ИТ-02",
        electrical_safety_group="III",
        can_be_internship_leader=True,
        internship_period_days=10
    )

    pos_dev = Position.objects.create(
        position_name="Разработчик",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_dev,
        safety_instructions_numbers="ОТ-01, ИТ-01",
        electrical_safety_group="II",
        internship_period_days=5
    )

    # Отдел тестирования
    pos_qa_lead = Position.objects.create(
        position_name="Руководитель отдела тестирования",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_qa,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, ИТ-01",
        electrical_safety_group="III",
        can_be_internship_leader=True,
        internship_period_days=14
    )

    pos_qa = Position.objects.create(
        position_name="Тестировщик",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_qa,
        safety_instructions_numbers="ОТ-01, ИТ-01",
        electrical_safety_group="II",
        internship_period_days=5
    )

    # Финансовый департамент
    pos_fin_director = Position.objects.create(
        position_name="Финансовый директор",
        organization=org1,
        subdivision=sub_finance_1,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, ФИН-01",
        electrical_safety_group="II",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    pos_accountant = Position.objects.create(
        position_name="Бухгалтер",
        organization=org1,
        subdivision=sub_finance_1,
        department=dept_accounting,
        safety_instructions_numbers="ОТ-01, ФИН-01",
        electrical_safety_group="II",
        internship_period_days=5
    )

    # HR-департамент
    pos_hr_director = Position.objects.create(
        position_name="Директор по персоналу",
        organization=org1,
        subdivision=sub_hr_1,
        is_responsible_for_safety=True,
        commission_role='secretary',
        safety_instructions_numbers="ОТ-01, HR-01",
        electrical_safety_group="II",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    pos_hr_specialist = Position.objects.create(
        position_name="HR-специалист",
        organization=org1,
        subdivision=sub_hr_1,
        department=dept_hr,
        safety_instructions_numbers="ОТ-01, HR-01",
        electrical_safety_group="II",
        internship_period_days=5
    )

    # --- Должности в АО "МедикалГруп" ---

    # Уровень организации
    pos_ceo_2 = Position.objects.create(
        position_name="Генеральный директор",
        organization=org2,
        is_responsible_for_safety=True,
        commission_role='chairman',
        safety_instructions_numbers="ОТ-01, ОТ-02, ПБ-01",
        electrical_safety_group="V",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    # Клиническое отделение
    pos_clinic_head = Position.objects.create(
        position_name="Главный врач",
        organization=org2,
        subdivision=sub_clinic,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, МЕД-01, МЕД-02",
        electrical_safety_group="IV",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    # Терапевтическое отделение
    pos_therapist = Position.objects.create(
        position_name="Терапевт",
        organization=org2,
        subdivision=sub_clinic,
        department=dept_therapy,
        safety_instructions_numbers="ОТ-01, МЕД-01",
        electrical_safety_group="II",
        internship_period_days=14
    )

    # Хирургическое отделение
    pos_surgeon = Position.objects.create(
        position_name="Хирург",
        organization=org2,
        subdivision=sub_clinic,
        department=dept_surgery,
        safety_instructions_numbers="ОТ-01, МЕД-01, МЕД-03",
        electrical_safety_group="III",
        internship_period_days=21
    )

    # Научно-исследовательский центр
    pos_research_head = Position.objects.create(
        position_name="Руководитель НИЦ",
        organization=org2,
        subdivision=sub_research,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, НИЦ-01, НИЦ-02",
        electrical_safety_group="IV",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    pos_researcher = Position.objects.create(
        position_name="Научный сотрудник",
        organization=org2,
        subdivision=sub_research,
        department=dept_research,
        safety_instructions_numbers="ОТ-01, НИЦ-01",
        electrical_safety_group="III",
        internship_period_days=14
    )

    # --- Должности в ЗАО "СтройКомплекс" ---

    # Уровень организации
    pos_ceo_3 = Position.objects.create(
        position_name="Генеральный директор",
        organization=org3,
        is_responsible_for_safety=True,
        commission_role='chairman',
        safety_instructions_numbers="ОТ-01, ОТ-02, ПБ-01",
        electrical_safety_group="V",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    # Строительный департамент
    pos_constr_head = Position.objects.create(
        position_name="Руководитель строительного департамента",
        organization=org3,
        subdivision=sub_construction,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, СТР-01, СТР-02",
        electrical_safety_group="IV",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    pos_builder = Position.objects.create(
        position_name="Строитель",
        organization=org3,
        subdivision=sub_construction,
        department=dept_construction,
        safety_instructions_numbers="ОТ-01, СТР-01, СТР-03",
        electrical_safety_group="III",
        internship_period_days=14
    )

    # Проектный департамент
    pos_design_head = Position.objects.create(
        position_name="Руководитель проектного департамента",
        organization=org3,
        subdivision=sub_design,
        is_responsible_for_safety=True,
        commission_role='member',
        safety_instructions_numbers="ОТ-01, ПРО-01",
        electrical_safety_group="III",
        can_be_internship_leader=True,
        internship_period_days=0
    )

    pos_architect = Position.objects.create(
        position_name="Архитектор",
        organization=org3,
        subdivision=sub_design,
        department=dept_design,
        safety_instructions_numbers="ОТ-01, ПРО-01, ПРО-02",
        electrical_safety_group="II",
        internship_period_days=10
    )

    # ========== 5. СОЗДАЕМ СОТРУДНИКОВ ==========

    # Сотрудники ООО "ТехноИнновации"
    Employee.objects.create(
        full_name_nominative="Иванов Иван Иванович",
        full_name_dative="Иванову Ивану Ивановичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 10),
        place_of_residence="г. Москва, ул. Центральная, д. 1, кв. 10",
        organization=org1,
        position=pos_ceo_1,
        height="182-188 см",
        clothing_size="52-54",
        shoe_size="44"
    )

    Employee.objects.create(
        full_name_nominative="Петров Петр Петрович",
        full_name_dative="Петрову Петру Петровичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 5),
        place_of_residence="г. Москва, ул. Ленина, д. 15, кв. 42",
        organization=org1,
        subdivision=sub_it_1,
        position=pos_it_director,
        height="170-176 см",
        clothing_size="48-50",
        shoe_size="42"
    )

    Employee.objects.create(
        full_name_nominative="Сидоров Алексей Викторович",
        full_name_dative="Сидорову Алексею Викторовичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 3),
        place_of_residence="г. Москва, ул. Пушкина, д. 7, кв. 18",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_dev,
        position=pos_dev_lead,
        height="182-188 см",
        clothing_size="52-54",
        shoe_size="45"
    )

    Employee.objects.create(
        full_name_nominative="Козлова Екатерина Александровна",
        full_name_dative="Козловой Екатерине Александровне",
        date_of_birth=birth_date_base - timedelta(days=365 * 3 + 180),
        place_of_residence="г. Москва, Ленинский пр-т, д. 112, кв. 54",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_dev,
        position=pos_senior_dev,
        height="158-164 см",
        clothing_size="44-46",
        shoe_size="37"
    )

    Employee.objects.create(
        full_name_nominative="Смирнова Анна Владимировна",
        full_name_dative="Смирновой Анне Владимировне",
        date_of_birth=birth_date_base - timedelta(days=365 * 2),
        place_of_residence="г. Москва, ул. Гагарина, д. 25, кв. 17",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_qa,
        position=pos_qa,
        height="158-164 см",
        clothing_size="44-46",
        shoe_size="38"
    )

    Employee.objects.create(
        full_name_nominative="Кузнецов Дмитрий Сергеевич",
        full_name_dative="Кузнецову Дмитрию Сергеевичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 7),
        place_of_residence="г. Москва, Комсомольский пр-т, д. 35, кв. 12",
        organization=org1,
        subdivision=sub_finance_1,
        position=pos_fin_director,
        height="170-176 см",
        clothing_size="50-52",
        shoe_size="43"
    )

    # Сотрудники АО "МедикалГруп"
    Employee.objects.create(
        full_name_nominative="Соколов Михаил Андреевич",
        full_name_dative="Соколову Михаилу Андреевичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 12),
        place_of_residence="г. Москва, пр-т Мира, д. 76, кв. 15",
        organization=org2,
        position=pos_ceo_2,
        height="182-188 см",
        clothing_size="52-54",
        shoe_size="44"
    )

    Employee.objects.create(
        full_name_nominative="Новикова Ольга Дмитриевна",
        full_name_dative="Новиковой Ольге Дмитриевне",
        date_of_birth=birth_date_base - timedelta(days=365 * 8),
        place_of_residence="г. Москва, ул. Тверская, д. 18, кв. 45",
        organization=org2,
        subdivision=sub_clinic,
        position=pos_clinic_head,
        height="158-164 см",
        clothing_size="44-46",
        shoe_size="38"
    )

    Employee.objects.create(
        full_name_nominative="Морозов Виктор Алексеевич",
        full_name_dative="Морозову Виктору Алексеевичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 6),
        place_of_residence="г. Москва, Кутузовский пр-т, д. 32, кв. 78",
        organization=org2,
        subdivision=sub_clinic,
        department=dept_surgery,
        position=pos_surgeon,
        height="170-176 см",
        clothing_size="48-50",
        shoe_size="42"
    )

    # Сотрудники ЗАО "СтройКомплекс"
    Employee.objects.create(
        full_name_nominative="Волков Андрей Игоревич",
        full_name_dative="Волкову Андрею Игоревичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 15),
        place_of_residence="Московская обл., г. Пушкино, ул. Лесная, д. 5, кв. 12",
        organization=org3,
        position=pos_ceo_3,
        height="182-188 см",
        clothing_size="56-58",
        shoe_size="46"
    )

    Employee.objects.create(
        full_name_nominative="Лебедев Николай Петрович",
        full_name_dative="Лебедеву Николаю Петровичу",
        date_of_birth=birth_date_base - timedelta(days=365 * 9),
        place_of_residence="Московская обл., г. Пушкино, ул. Центральная, д. 18, кв. 5",
        organization=org3,
        subdivision=sub_construction,
        position=pos_constr_head,
        height="170-176 см",
        clothing_size="52-54",
        shoe_size="44"
    )

    # ========== 6. СОЗДАЕМ ДОКУМЕНТЫ ==========

    # Документы ООО "ТехноИнновации"
    Document.objects.create(
        name="Устав ООО 'ТехноИнновации'",
        organization=org1
    )

    Document.objects.create(
        name="Инструкция по охране труда для IT-специалистов",
        organization=org1,
        subdivision=sub_it_1
    )

    Document.objects.create(
        name="Регламент разработки ПО",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_dev
    )

    # Документы АО "МедикалГруп"
    Document.objects.create(
        name="Устав АО 'МедикалГруп'",
        organization=org2
    )

    Document.objects.create(
        name="Лицензия на осуществление медицинской деятельности",
        organization=org2,
        subdivision=sub_clinic
    )

    # Документы ЗАО "СтройКомплекс"
    Document.objects.create(
        name="Устав ЗАО 'СтройКомплекс'",
        organization=org3
    )

    Document.objects.create(
        name="Разрешение на строительство жилого комплекса 'Заречный'",
        organization=org3,
        subdivision=sub_construction
    )

    Document.objects.create(
        name="Проектная документация 'Жилой дом по ул. Центральная'",
        organization=org3,
        subdivision=sub_design,
        department=dept_design
    )

    # ========== 7. СОЗДАЕМ ОБОРУДОВАНИЕ ==========

    # Оборудование ООО "ТехноИнновации"
    Equipment.objects.create(
        equipment_name="Сервер Dell PowerEdge R740",
        inventory_number="TI-SRV-001",
        organization=org1,
        subdivision=sub_it_1
    )

    Equipment.objects.create(
        equipment_name="Ноутбук Dell XPS 15",
        inventory_number="TI-LPT-001",
        organization=org1,
        subdivision=sub_it_1,
        department=dept_dev
    )

    Equipment.objects.create(
        equipment_name="МФУ HP LaserJet Enterprise",
        inventory_number="TI-PRN-001",
        organization=org1,
        subdivision=sub_finance_1
    )

    # Оборудование АО "МедикалГруп"
    Equipment.objects.create(
        equipment_name="УЗИ аппарат Philips Affiniti 70",
        inventory_number="MG-USG-001",
        organization=org2,
        subdivision=sub_clinic
    )

    Equipment.objects.create(
        equipment_name="Операционный стол Maquet",
        inventory_number="MG-SRG-001",
        organization=org2,
        subdivision=sub_clinic,
        department=dept_surgery
    )

    # Оборудование ЗАО "СтройКомплекс"
    Equipment.objects.create(
        equipment_name="Башенный кран Liebherr 154 EC-H",
        inventory_number="SC-CRN-001",
        organization=org3,
        subdivision=sub_construction
    )

    Equipment.objects.create(
        equipment_name="3D принтер для макетов Ultimaker S5",
        inventory_number="SC-3DP-001",
        organization=org3,
        subdivision=sub_design,
        department=dept_design
    )


def delete_demo_data(apps, schema_editor):
    """
    Удаление всех демонстрационных данных при откате миграции.
    """
    Organization = apps.get_model('directory', 'Organization')
    Organization.objects.all().delete()
    # Каскадное удаление удалит связанные записи во всех других таблицах


class Migration(migrations.Migration):
    dependencies = [
        # Укажите здесь вашу последнюю примененную миграцию
        ('directory', '0001_initial'),  # Замените на актуальную
    ]

    operations = [
        migrations.RunPython(create_demo_data, delete_demo_data),
    ]