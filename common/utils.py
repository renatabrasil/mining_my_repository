# # third-party
import logging
import unicodedata
from typing import Optional

from contributions import models

logger = logging.getLogger(__name__)


class CommitUtils(object):

    @staticmethod
    def get_email(full_email: str):
        """
        Emails in the form of: "john doe at gmail dot com"
        Should return johndoe@gmail.com

        Parameters:
            full_email(str): unformatted email
        Returns:
            str: formatted email
        """

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
        """Returns the right path based on the old_path, the new_path, and the type of modification of the file modified in a commit

        Parameters:
            modification(Modification): file changed in a commit

        Returns:
            str: the final path of the file

        """
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
        """
        Removes accents and special characters from a given name

        Parameters:
            name(str): name with or without special characters

        Returns:
            str: the same given name without special characters
        """
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
        """
        Receives the path of a file and returns the directory where it is

        Parameters:
            path(str): complete path of a file
        Returns:
            str: directory path
        """
        index = path.rfind("/")
        if index > -1:
            directory_str = path[:index]
        else:
            directory_str = "/"

        return directory_str

    @staticmethod
    def is_java_file(path: Optional[str]) -> bool:
        """
        Checks if a given file is a java file

        Parameters:
            path(str): path of a file

        Returns:
            bool: true if it is a java file
        """
        if path:
            index = path.rfind(".")
            if index > -1:
                return path[index:] == ".java"
        return False


class ViewUtils(object):
    """
    Methods to be used in views
    """

    @staticmethod
    def load_tag(request):
        """
        Should load the tag that is stored in session.
        If it is not possible, to avoid errors, should return the first tag of the first project in the database

        Parameters:
            request(request): request of a view
        Returns:
            Tag: the tag object

        """
        try:
            tag_id = request.session.get('tag', None)
            if 'tag' in request.POST:
                tag_id = request.POST.get('tag')
            elif not tag_id and 'tag' in request.GET:
                tag_id = models.Tag.objects.filter(description=request.GET.get('tag')).first().get('id', None)

            if not tag_id:
                raise ValueError("Enter in admin session and provide a project and a tag belong to it.")
            request.session['tag'] = tag_id
            return models.Tag.objects.filter(pk=tag_id).first()
        except Exception as e:
            logger.exception(e.args[0])
            logger.error("Enter in admin session and provide a project and a tag belong to it.")
            raise
