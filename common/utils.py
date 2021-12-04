# # third-party
import unicodedata

from django.http import HttpRequest

from contributions import models


class CommitUtils(object):

    @staticmethod
    def get_email(full_email: str):
        '''
        Emails in the form of: "john doe at gmail dot com"
        Should return johndoe@gmail.com

        Parameters:
            full_email(str): unformatted email
        Returns:
            str: formatted email
        '''

        array_email = full_email.split(" ")
        email = ''
        for part in array_email:
            if part.lower() == 'at':
                email += '@'
            elif part.lower() == 'dot':
                email += '.'
            elif part.lower() == 'dash':
                email += '-'
            elif part.lower() == 'minus':
                email += '-'
            else:
                email += part

        return email.lower()

    @staticmethod
    def true_path(modification: 'Modification'):
        '''Returns the right path based on the old_path, the new_path, and the type of modification of the file modified in a commit

        Parameters:
            modification(Modification): file changed in a commit

        Returns:
            str: the final path of the file

        '''
        old_path = ''
        new_path = ''

        if modification.old_path:
            old_path = modification.old_path.replace("\\", "/")
        if modification.new_path:
            new_path = modification.new_path.replace("\\", "/")
        if modification.change_type.name == 'DELETE':
            path = old_path
        else:
            path = new_path

        return path

    @staticmethod
    def strip_accents(name: str):
        '''
        Removes accents and special characters from a given name

        Parameters:
            name(str): name with or without special characters

        Returns:
            str: the same given name without special characters
        '''
        try:
            name = unicode(name, 'utf-8')
        except NameError:  # unicode is a default on python 3
            pass

        name = unicodedata.normalize('NFD', name) \
            .encode('ascii', 'ignore') \
            .decode("utf-8")

        return str(name)

    @staticmethod
    def extract_directory_name_from_full_file_name(path: str):
        '''
        Receives the path of a file and returns the directory where it is

        Parameters:
            path(str): complete path of a file
        Returns:
            str: directory path
        '''
        index = path.rfind("/")
        directory_str = ""
        if index > -1:
            directory_str = path[:index]
        else:
            directory_str = "/"

        return directory_str

    @staticmethod
    def is_java_file(path: str):
        '''
        Checks if a given file is a java file

        Parameters:
            path(str): path of a file

        Returns:
            bool: true if it is a java file
        '''
        if path:
            index = path.rfind(".")
            if index > -1:
                return path[index:] == ".java"
        return False


class ViewUtils(object):
    '''
    Methods to be used in views
    '''

    @staticmethod
    def load_tag(request):
        '''
        Should load the tag that is stored in session.
        If it is not possible, to avoid errors, should return the first tag of the first project in the database

        Parameters:
            request(request): request of a view
        Returns:
            Tag: the tag object

        '''
        tag_id = request.POST.get('tag')

        if not tag_id:
            try:
                tag_id = request.session['tag']
            except Exception as e:
                print(str(e))
                tag_id = models.Tag.objects.filter(project=request.session['project']).first().id
        query = models.Tag.objects.filter(pk=tag_id)
        if not tag_id:
            tag_description = request.GET.get('tag')
            query = models.Tag.objects.filter(description=tag_description)
        else:
            request.session['tag'] = tag_id
        tag = None
        if query.count() > 0:
            tag = query[0]
        return tag

    @staticmethod
    def get_current_project(request):
        '''
        Should return the first project that exists in the database.

        This method is used to prevent an exception in the presentation layer because it requires a project.

        Throws an exception if there is no model in database

        Parameters:
            request(HttpRequest):

        Return:
            Project: the first project in database

        Raises:
            Exception: if there is no model in database

        '''
        try:
            return models.Project.objects.all().first()
        except Exception as e:
            raise Exception(e)
