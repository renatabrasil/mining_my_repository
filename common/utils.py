from contributions import models

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