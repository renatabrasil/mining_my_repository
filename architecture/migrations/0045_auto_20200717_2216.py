import re

from django.db import migrations
from pydriller import GitRepository


def detect_impact_loc(code):
    total_lines = code.count('\n')
    commented_lines = 0
    blank_lines = 0
    uncommented_lines = 0
    if total_lines > 0:
        # FIXME: Put this part on loop below
        lines = code.split("\n")
        # In case we should consider commented lines
        for line in lines:
            found = ''
            found2 = ''
            m = re.search(r"\u002F/.*", line)
            n = re.search(r'(\/\*([^*]|[\r\n]|(\*+([^*\/]|[\r\n]))){0,100}\*+\/)|\/{0,1}[^0-9][a-zA-Z]*\*[^;]([^0-9][a-zA-Z]+)[^\r\n]*', line)
            if m or n:
                if m:
                    found = m.group(0)
                    line = re.sub(r'\u002F/.*', '', found)
                    line.replace(' ', '', 1)
                    if line.strip().isdigit():
                        commented_lines += 1
                elif n:
                    found = n.group(0)
                    line = re.sub(r'(\/\*([^*]|[\r\n]|(\*+([^*\/]|[\r\n]))){0,100}\*+\/)|\/{0,1}[^0-9][a-zA-Z]*\*[^;]([^0-9][a-zA-Z]+)[^\r\n]*',
                                  '',
                                  found)
                    line.replace(' ', '', 1)
                    if line.strip().isdigit():
                        commented_lines += 1
            elif not line.replace(" ", "").isdigit() and (line != '' and line != '\n'):
                return True

    return False

class Migration(migrations.Migration):

    def update_has_impact_code(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        Modification = apps.get_model('contributions', 'Modification')
        Commit = apps.get_model('contributions', 'Commit')

        for mod in Modification.objects.all():
            GR = GitRepository(mod.commit.tag.project.project_path)

            diff_text = GR.parse_diff(mod.diff)

            added_text = ""
            for line in diff_text['added']:
                added_text = added_text + "\n" + str(line[0]) + ' ' + "" + ' ' + line[1]

            deleted_text = ""
            for line in diff_text['deleted']:
                deleted_text = deleted_text + "\n" + str(line[0]) + ' ' + "" + ' ' + line[1]

            added_uncommented_lines = detect_impact_loc(added_text)
            deleted_uncommented_lines = detect_impact_loc(deleted_text)
            mod.has_impact_loc = added_uncommented_lines or deleted_uncommented_lines

            mod.save()

    dependencies = [
        ('architecture', '0042_auto_20200713_2132'),
    ]

    operations = [
        migrations.RunPython(update_has_impact_code),
    ]