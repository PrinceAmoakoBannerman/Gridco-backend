from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django import forms

User = get_user_model()


class ForcePasswordForm(forms.ModelForm):
    force_initial_password = forms.BooleanField(required=False, label='Force initial password (leave account with unusable password)')

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    change_form_template = 'admin/auth/user/change_form.html'

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)
        # inject our extra field into the admin form
        class WrappedForm(Form, ForcePasswordForm):
            pass

        return WrappedForm

    def save_model(self, request, obj, form, change):
        # if admin checked the force_initial_password box, set an unusable password
        try:
            if form.cleaned_data.get('force_initial_password'):
                obj.set_unusable_password()
        except Exception:
            pass
        super().save_model(request, obj, form, change)
