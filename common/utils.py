# # third-party
import itertools
import math
import unicodedata
import unidecode

# local Django
from contributions import models

class CommitUtils(object):

    # From: https://stackoverflow.com/questions/5110177/how-to-convert-floating-point-number-to-base-3-in-python
    @staticmethod
    def convert_base(x, base=3, precision=None):
        length_of_int = int(math.log(x, base))
        iexps = range(length_of_int, -1, -1)
        if precision == None:
            fexps = itertools.count(-1, -1)
        else:
            fexps = range(-1, -int(precision + 1), -1)

        def cbgen(x, base, exponents):
            for e in exponents:
                d = int(x // (base ** e))
                x -= d * (base ** e)
                yield d
                if x == 0 and e < 0: break

        return cbgen(int(x), base, iexps), cbgen(x - int(x), base, fexps)

    @staticmethod
    def get_email(full_email):
        """"In the form of: <john doe at gmail dot com>
        Returns johndoe@gmail.com"""
        array_email = full_email.split(" ")
        # email = email[0]+"@"+email[2]+"."+email[4]
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
    # regex ([a-zA-Z0-9_.+-]+\s*at+\s*[a-zA-Z0-9-]+\s*dot\s*[a-zA-Z0-9-.]+)

    @staticmethod
    def true_path(modification):
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
    def strip_accents(text):

        try:
            text = unicode(text, 'utf-8')
        except NameError:  # unicode is a default on python 3
            pass

        text = unicodedata.normalize('NFD', text) \
            .encode('ascii', 'ignore') \
            .decode("utf-8")

        return str(text)

    @staticmethod
    def directory_to_str(path):
        index = path.rfind("/")
        directory_str = ""
        if index > -1:
            directory_str = path[:index]
        else:
            directory_str = "/"

        return directory_str


    @staticmethod
    def modification_is_java_file(path):
        if path:
            index = path.rfind(".")
            if index > -1:
                return path[index:] == ".java"
        return False

class ViewUtils(object):

    @staticmethod
    def load_tag(request):
        tag_id = request.POST.get('tag')

        if not tag_id:
            try:
                tag_id = request.session['tag']
            except Exception as e:
                # raise  # reraises the exceptio
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
    def current_project(request):
        return models.Project.objects.all().first()
