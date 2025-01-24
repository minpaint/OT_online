from import_export import resources
from import_export.fields import Field
from .models import Organization, Department, Division, Position, Employee

class OrganizationResource(resources.ModelResource):
    class Meta:
        model = Organization
        fields = ('id', 'name_ru', 'short_name_ru', 'name_by', 'short_name_by', 
                 'inn', 'requisites_ru', 'requisites_by')
        import_id_fields = ['inn']

class DepartmentResource(resources.ModelResource):
    organization_inn = Field(attribute='organization__inn', column_name='organization_inn')

    class Meta:
        model = Department
        fields = ('id', 'name', 'organization_inn')
        import_id_fields = ['name', 'organization_inn']

    def before_import_row(self, row, **kwargs):
        inn = row.get('organization_inn')
        if inn:
            org = Organization.objects.filter(inn=inn).first()
            if org:
                row['organization'] = org.id

class DivisionResource(resources.ModelResource):
    department_name = Field(attribute='department__name', column_name='department_name')
    organization_inn = Field(attribute='department__organization__inn', 
                           column_name='organization_inn')

    class Meta:
        model = Division
        fields = ('id', 'name', 'department_name', 'organization_inn')
        import_id_fields = ['name', 'department_name', 'organization_inn']

    def before_import_row(self, row, **kwargs):
        org_inn = row.get('organization_inn')
        dept_name = row.get('department_name')
        if org_inn and dept_name:
            dept = Department.objects.filter(
                name=dept_name,
                organization__inn=org_inn
            ).first()
            if dept:
                row['department'] = dept.id

class PositionResource(resources.ModelResource):
    class Meta:
        model = Position
        fields = ('id', 'name', 'is_electrical_personnel', 'electrical_safety_group',
                 'is_internship_supervisor', 'internship_period')
        import_id_fields = ['name']

class EmployeeResource(resources.ModelResource):
    position_name = Field(attribute='position__name', column_name='position_name')
    division_name = Field(attribute='division__name', column_name='division_name')
    department_name = Field(attribute='division__department__name', 
                          column_name='department_name')
    organization_inn = Field(attribute='division__department__organization__inn',
                           column_name='organization_inn')

    class Meta:
        model = Employee
        fields = ('id', 'last_name', 'first_name', 'middle_name', 
                 'position_name', 'division_name', 'department_name',
                 'organization_inn', 'employment_date')
        import_id_fields = ['last_name', 'first_name', 'position_name', 
                          'division_name']

    def before_import_row(self, row, **kwargs):
        org_inn = row.get('organization_inn')
        dept_name = row.get('department_name')
        div_name = row.get('division_name')
        pos_name = row.get('position_name')

        if all([org_inn, dept_name, div_name, pos_name]):
            division = Division.objects.filter(
                name=div_name,
                department__name=dept_name,
                department__organization__inn=org_inn
            ).first()
            position = Position.objects.filter(name=pos_name).first()

            if division and position:
                row['division'] = division.id
                row['position'] = position.id
