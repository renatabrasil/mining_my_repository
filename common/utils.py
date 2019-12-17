import re

import unidecode

from contributions import models
import unicodedata

class CommitUtils(object):

    @staticmethod
    def true_path(modification):
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
    def count_uncommented_lines(code):
        total_lines = code.count('\n')
        commented_lines = 0
        lines = code.split("\n")
        for line in lines:
            m = re.search(r"\u002F/.*", line)
            found = ''
            if m:
                found = m.group(0)
                if found:
                    line = re.sub(r'\u002F/.*','',line)
                    line.replace(' ','',1)
                    if line.strip().isdigit():
                        commented_lines += 1

        comments = [x.group() for x in re.finditer(r"(\/\*([^*]|[\r\n]|(\*+([^*\/]|[\r\n])))*\*+\/)|(\/\/.*)'.*?\n|\*[^;][\s\S][^\r\n]*", code)]
        for comment in comments:
            commented_lines += comment.count('\n')
            commented_lines += 1

        return total_lines - (commented_lines + CommitUtils.count_blank_lines(code))

    @staticmethod
    def get_commented_lines(code):
        m = re.search(r"(\/\*([^*]|[\r\n]|(\*+([^*\/]|[\r\n])))*\*+\/)|(\/\/.*)'.*?\n|\*[^;][\s\S][^\r\n]*", code)
        found = ''
        if m:
            found = m.group(1)
            if not found:
                return ''
        return found

    @staticmethod
    def count_blank_lines(code):
        total_lines = code.count('\n')
        blank_lines = 0
        code = code.replace(CommitUtils.get_commented_lines(code).replace('\n',''), '')
        lines = code.split('\n')
        for line in lines[1:]:
            if not line.strip():
                blank_lines += 1
            elif line.replace(" ","").isdigit():
                blank_lines += 1
        return blank_lines

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
                tag_id = models.Tag.objects.all().first().id
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