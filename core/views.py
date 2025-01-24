from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView,
    DetailView
)
from django.http import FileResponse
from .models import (
    Organization,
    Position,
    Employee,
    Document,
    OrganizationalUnit
)
from .forms import (
    OrganizationForm,
    PositionForm,
    EmployeeForm,
    DocumentForm,
    OrganizationalUnitForm
)

# OrganizationalUnit Views
class OrganizationalStructureView(LoginRequiredMixin, ListView):
    model = OrganizationalUnit
    template_name = 'core/organizational_structure.html'
    context_object_name = 'nodes'

    def get_queryset(self):
        return OrganizationalUnit.objects.all()

class OrganizationalUnitListView(LoginRequiredMixin, ListView):
    model = OrganizationalUnit
    template_name = 'core/organizational_unit_list.html'
    context_object_name = 'units'

class OrganizationalUnitCreateView(LoginRequiredMixin, CreateView):
    model = OrganizationalUnit
    form_class = OrganizationalUnitForm
    template_name = 'core/organizational_unit_form.html'
    success_url = reverse_lazy('core:organizational_unit_list')

class OrganizationalUnitUpdateView(LoginRequiredMixin, UpdateView):
    model = OrganizationalUnit
    form_class = OrganizationalUnitForm
    template_name = 'core/organizational_unit_form.html'
    success_url = reverse_lazy('core:organizational_unit_list')

class OrganizationalUnitDeleteView(LoginRequiredMixin, DeleteView):
    model = OrganizationalUnit
    success_url = reverse_lazy('core:organizational_unit_list')

# Organization Views
class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    context_object_name = 'organizations'
    template_name = 'core/organization_list.html'

class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'core/organization_form.html'
    success_url = reverse_lazy('core:organization_list')

class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'core/organization_form.html'
    success_url = reverse_lazy('core:organization_list')

class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    model = Organization
    success_url = reverse_lazy('core:organization_list')

# Position Views
class PositionListView(LoginRequiredMixin, ListView):
    model = Position
    context_object_name = 'positions'
    template_name = 'core/position_list.html'

    def get_queryset(self):
        queryset = Position.objects.all()
        unit_id = self.request.GET.get('unit')
        if unit_id:
            queryset = queryset.filter(organizational_unit_id=unit_id)
        return queryset

class PositionCreateView(LoginRequiredMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'core/position_form.html'
    success_url = reverse_lazy('core:position_list')

class PositionUpdateView(LoginRequiredMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'core/position_form.html'
    success_url = reverse_lazy('core:position_list')

class PositionDeleteView(LoginRequiredMixin, DeleteView):
    model = Position
    success_url = reverse_lazy('core:position_list')

# Employee Views
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    context_object_name = 'employees'
    template_name = 'core/employee_list.html'

    def get_queryset(self):
        queryset = Employee.objects.all()
        position_id = self.request.GET.get('position')
        if position_id:
            queryset = queryset.filter(position_id=position_id)
        return queryset

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'core/employee_form.html'
    success_url = reverse_lazy('core:employee_list')

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'core/employee_form.html'
    success_url = reverse_lazy('core:employee_list')

class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy('core:employee_list')

# Document Views
class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    context_object_name = 'documents'
    template_name = 'core/document_list.html'

class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'core/document_form.html'
    success_url = reverse_lazy('core:document_list')

class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'core/document_form.html'
    success_url = reverse_lazy('core:document_list')

class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document
    success_url = reverse_lazy('core:document_list')

class DocumentDownloadView(LoginRequiredMixin, DetailView):
    model = Document

    def get(self, request, *args, **kwargs):
        document = self.get_object()
        response = FileResponse(document.file, as_attachment=True)
        return response