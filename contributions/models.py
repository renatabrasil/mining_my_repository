from django.db import models

# Create your models here.

class Developer(models.Model):
	name = models.CharField(max_length=200)
	email = models.CharField(max_length=200)
    # def __str__(self):
    #     return self.name

class Project(models.Model):
	project_name = models.CharField(max_length=200)
	project_path = models.CharField(max_length=200)

class Commit(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='commits')
	hash = models.CharField(max_length=300)
	msg = models.CharField(max_length=300)
	author = models.ForeignKey(Developer, related_name='author_id', on_delete=models.CASCADE)
	author_date = models.DateField()
	committer = models.ForeignKey(Developer, related_name='committer_id', on_delete=models.CASCADE)
	committer_date = models.DateField()
    # pub_date = models.DateTimeField('date published')

class Method(models.Model):
	name = models.CharField(max_length=150)

class Modification(models.Model):
	commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='modifications')
	old_path = models.CharField(max_length=100)
	new_path = models.CharField(max_length=100)
	ADDED = 'ADD'
	DELETED = 'DEL'
	MODIFIED = 'MOD'
	RENAMED = 'REN'
	CHANGE_TYPES_CHOICES = [
		(ADDED, 'Added'),
		(DELETED, 'Deleted'),
		(MODIFIED, 'Modified'),
		(RENAMED, 'Renamed'),
	]
	change_type = models.CharField(
		max_length=10,
		choices=CHANGE_TYPES_CHOICES,
		default=MODIFIED,
	)
	diff = models.TextField()
	source_code = models.TextField()
	source_code_before = models.TextField()
	added = models.IntegerField()
	removed = models.IntegerField()
	nloc = models.IntegerField()
	complexity = models.IntegerField()
	token_count = models.IntegerField()

