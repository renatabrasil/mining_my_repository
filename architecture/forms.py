from django import forms

class FilesCompiledForm(forms.Form):
    # directory = forms.CharField(label='Diretorio', max_length=100)
    git_local_repository = forms.CharField(label='Local repository', max_length=200)
    directory = forms.CharField(label='Diretorio', max_length=100)
    build_path = forms.CharField(label='Build path', max_length=100)
    # widget = forms.TextInput(attrs={'class': 'myfieldclass'})
    project_id = forms.IntegerField(widget = forms.HiddenInput(), required = False)

    def __init__(self, *args, **kwargs):
        super(FilesCompiledForm, self).__init__(*args, **kwargs)
        self.fields['directory'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter directory name'})
        self.fields['git_local_repository'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter local repository name where compiled will be created'})
        self.fields['build_path'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Directory of compiled classes'})