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

	@property
	def number_of_java_files(self):
		total_java_files = 0
		for modification in self.modifications.all():
			if modification.is_java_file:
				total_java_files = total_java_files + 1
		return total_java_files


class Method(models.Model):
	name = models.CharField(max_length=150)

class Modification(models.Model):
	commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='modifications')
	old_path = models.CharField(max_length=200, null=True)
	new_path = models.CharField(max_length=200, null=True)
	path = models.CharField(max_length=200, null=True, default="-")
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
	source_code = models.TextField(null=True)
	source_code_before = models.TextField(null=True)
	added = models.IntegerField(null=True)
	removed = models.IntegerField(null=True)
	delta = models.IntegerField(default=0)
	nloc = models.IntegerField(null=True)
	complexity = models.IntegerField(null=True)
	token_count = models.CharField(max_length=200,null=True)

	@property
	def directory(self):
		index = self.path.rfind("/")
		if index > -1:
			return self.path[:index]
		return self.path

	@property
	def file(self):
		index = self.path.rfind("/")
		if index > -1:
			return self.path[index+1:]
		return self.path

	@property
	def is_java_file(self):
		if self.path:
			index = self.path.rfind(".")
			if index > -1:
				return self.path[index:] == ".java"
		return False


	def save(self, *args, **kwargs):
		if self.old_path:
			self.old_path = self.old_path.replace("\\","/")
		if self.new_path:
			self.new_path = self.new_path.replace("\\", "/")
		if self.change_type == "ModificationType.DEL":
			self.path = self.old_path
		else:
			self.path = self.new_path

		self.delta = abs(self.added-self.removed)
		super().save(*args, **kwargs)  # Call the "real" save() method.


