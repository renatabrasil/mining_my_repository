# Django
from django import forms


class FilesCompiledForm(forms.Form):
    git_local_repository = forms.CharField(label='Local repository', max_length=300)
    directory = forms.CharField(label='Diretorio', max_length=100)
    build_path = forms.CharField(label='Build path', max_length=100)
    project_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(FilesCompiledForm, self).__init__(*args, **kwargs)
        self.fields['directory'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Enter directory name', 'value': 'compiled'})
        self.fields['git_local_repository'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Enter local repository name where compiled will be created',
             'value': 'C:/Users/renat/OneDrive/Documentos/Projetos/repositories'})
        self.fields['build_path'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Directory of compiled classes', 'value': 'build/classes'})
