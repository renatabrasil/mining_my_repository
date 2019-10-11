from django.db import models
import numpy as np

# Create your models here.

class Developer(models.Model):
	name = models.CharField(max_length=200)
	email = models.CharField(max_length=200)

	def __str__(self):
		return self.name + '('+self.email+')'

class Project(models.Model):
	project_name = models.CharField(max_length=200)
	project_path = models.CharField(max_length=200)

	def __str__(self):
		return self.project_name

class Tag(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tags')
	description = models.CharField(max_length=100)
	# previous_tag = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, default=None)
	previous_tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True, default=None)

	def __str__(self):
		return self.description

class Directory(models.Model):
	name = models.CharField(max_length=200)
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='directories')
	# parent_tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='directories')
	visible = models.BooleanField(default=True)


	def __str__(self):
		return self.name + " - Visible: " + str(self.visible)

class Commit(models.Model):
	tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='commits')
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='commits')
	hash = models.CharField(max_length=300)
	msg = models.CharField(max_length=300)
	author = models.ForeignKey(Developer, related_name='author_id', on_delete=models.CASCADE)
	author_date = models.DateField()
	committer = models.ForeignKey(Developer, related_name='committer_id', on_delete=models.CASCADE)
	committer_date = models.DateField()
    # pub_date = models.DateTimeField('date published')

	# def __eq__(self, other):
	# 	return isinstance(other, self.__class__) and self.hash == other.hash

	@property
	def number_of_java_files(self):
		total_java_files = 0
		for modification in self.modifications.all():
			if modification.is_java_file:
				total_java_files = total_java_files + 1
		return total_java_files


	def directories2(self):

		directoriesD =list()

		for modification in self.modifications.all():
			if modification.is_java_file:
				if modification.directory not in directoriesD:
					directoriesD.append(modification.directory)
		return directoriesD


class Method(models.Model):
	name = models.CharField(max_length=150)

class Modification(models.Model):
	commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='modifications')
	old_path = models.CharField(max_length=200, null=True)
	new_path = models.CharField(max_length=200, null=True)
	path = models.CharField(max_length=200, null=True, default="-")
	directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='modifications')
	# directory = models.CharField(max_length=200, null=True, default="-")
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
	cloc = models.IntegerField(default=0)
	nloc = models.IntegerField(null=True)
	complexity = models.IntegerField(null=True)
	# token_count = models.CharField(max_length=200,null=True)

	# def __eq__(self, other):
	# 	return isinstance(other, self.__class__) and (self.commit.hash == other.commit.hash and self.file == other.file)

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
		if self.change_type.name == 'DELETE':
			self.path = self.old_path
		else:
			self.path = self.new_path


		index = self.path.rfind("/")
		directory_str = ""
		if index > -1:
			directory_str = self.path[:index]
		else:
			directory_str = "/"

		# directory = Directory.objects.filter(name=directory_str)
		# if directory.count() == 0:
		# 	author = Directory(name=directory_str, email=commit_repository.author.email)
		# 	author.save()
		# else:
		# 	author = directory[0]

		# self.delta = abs(self.added-self.removed)
		self.cloc = self.added + self.removed
		super().save(*args, **kwargs)  # Call the "real" save() method.

class TransientModel(models.Model):
    """Inherit from this class to use django constructors and serialization but no database management"""
    def save(*args, **kwargs):
        pass  # avoid exceptions if called

    class Meta:
        abstract = True  # no table for this class
        managed = False  # no database management

class Contributor(TransientModel):
	abstract = True  # no table for this class
	managed = False  # no database management

	def __init__(self,developer):
		self.developer = developer
		self.loc_count = 0
		self.file_count = 0
		self.commit_count = 0
		self.total_loc = 0
		self.total_file = 0
		self.total_commit = 0
		self.commits = []
		self.files = []

	@property
	def loc_percentage(self):
		try:
			return self.loc_count/self.total_loc
		except ZeroDivisionError:
			return 0.0
	@property
	def file_percentage(self):
		try:
			return self.file_count / self.total_file
		except ZeroDivisionError:
			return 0.0
	@property
	def commit_percentage(self):
		try:
			return self.commit_count / self.total_commit
		except ZeroDivisionError:
			return 0.0

	@property
	def experience(self):
		try:
			return 0.4*self.commit_percentage + 0.4 * self.file_percentage + 0.2*self.loc_percentage
		except ZeroDivisionError:
			return 0.0

class ContributionByAuthorReport(TransientModel):
	abstract = True  # no table for this class
	managed = False  # no database management
	def __init__(self):
		self._commits_by_author = {}
		self._total_commits = 0
		self._total_java_files = 0
		self._total_loc = 0
		self.peripheral_developers = []
		self._core_developers_threshold_loc = 0.0
		self._core_developers_threshold_file = 0.0
		self._core_developers_threshold_commit = 0.0
		self._core_developers_threshold_experience = 0.0
		self._minor = 0
		self._major = 0

	@property
	def is_Empty(self):
		return not bool(self._commits_by_author)

	@property
	def ownership(self):
		higher_value = -1.0
		for contributor in self._commits_by_author.items():
			if contributor[1].commit_percentage >= higher_value:
				higher_value = contributor[1].commit_percentage
		return higher_value

	@property
	def minor(self):
		for contributor in self._commits_by_author.items():
			if contributor[1].commit_percentage <= 0.05:
				self._minor = self._minor + 1
		return self._minor

	@property
	def major(self):
		for contributor in self._commits_by_author.items():
			if contributor[1].commit_percentage > 0.05:
				self._major = self._major + 1
		return self._major

	@property
	def core_developers_files(self):
		core_developers = []
		for contributor in self._commits_by_author.items():
			if contributor[1].file_percentage > self._core_developers_threshold_file:
				core_developers.append(contributor[0])
		return core_developers

	@property
	def core_developers_commits(self):
		core_developers = []
		for contributor in self._commits_by_author.items():
			# TODO: check if it makes sense
			if len(self._commits_by_author) == 1:
				return [contributor[0]]
			if contributor[1].commit_percentage > self._core_developers_threshold_commit:
				core_developers.append(contributor[0])
		return core_developers

	@property
	def peripheral_developers_files(self):
		peripheral_developers = []
		for contributor in self._commits_by_author.items():
			if contributor[1].file_percentage <= self._core_developers_threshold_file:
				peripheral_developers.append(contributor[0])
		return peripheral_developers

	@property
	def peripheral_developers_commits(self):
		peripheral_developers = []
		for contributor in self._commits_by_author.items():
			if contributor[1].commit_percentage <= self._core_developers_threshold_commit:
				peripheral_developers.append(contributor[0])
		return peripheral_developers

	@property
	def core_developers_experience(self):
		core_developers = []
		for contributor in self._commits_by_author.items():
			# TODO: check if it makes sense
			if len(self._commits_by_author) == 1:
				return [contributor[0]]
			if contributor[1].experience > self._core_developers_threshold_experience:
				core_developers.append(contributor[0])
		return core_developers

	@property
	def peripheral_developers_files(self):
		peripheral_developers = []
		for contributor in self._commits_by_author.items():
			if contributor[1].file_percentage <= self._core_developers_threshold_file:
				peripheral_developers.append(contributor[0])
		return peripheral_developers

	@property
	def peripheral_developers_experience(self):
		peripheral_developers = []
		for contributor in self._commits_by_author.items():
			if contributor[1].experience <= self._core_developers_threshold_experience:
				peripheral_developers.append(contributor[0])
		return peripheral_developers

	@property
	def core_developers_threshold_file(self):
		file_count_array = []
		for contributor in self._commits_by_author.items():
			file_count_array.append(contributor[1].file_percentage)
		interval = np.array(file_count_array)
		if interval.any():
			self._core_developers_threshold_file = np.percentile(interval, 80)
		return self._core_developers_threshold_file

	@core_developers_threshold_file.setter
	def core_developers_threshold_file(self, core_developers_threshold_file):
		self._core_developers_threshold_file = core_developers_threshold_file

	@property
	def core_developers_threshold_commit(self):
		array = []
		for contributor in self._commits_by_author.items():
			array.append(contributor[1].commit_percentage)
		interval = np.array(array)
		if interval.any():
			self._core_developers_threshold_commit = np.percentile(interval, 80)
		return self._core_developers_threshold_commit


	@core_developers_threshold_commit.setter
	def core_developers_threshold_commit(self, core_developers_threshold_commit):
		self._core_developers_threshold_commit = core_developers_threshold_commit

	@property
	def core_developers_threshold_experience(self):
		experience_count_array = []
		for contributor in self._commits_by_author.items():
			experience_count_array.append(contributor[1].experience)
		interval = np.array(experience_count_array)
		if interval.any():
			self._core_developers_threshold_experience = np.percentile(interval, 80)
		return self._core_developers_threshold_experience

	@core_developers_threshold_experience.setter
	def core_developers_threshold_experience(self, core_developers_threshold_experience):
		self._core_developers_threshold_experience = core_developers_threshold_experience

	@property
	def commits_by_author(self):
		return self._commits_by_author

	@commits_by_author.setter
	def commits_by_author(self, commits_by_author):
		self._commits_by_author = commits_by_author

	@property
	def total_commits(self):
		return self._total_commits

	@total_commits.setter
	def total_commits(self, total_commits):
		for contributor in self._commits_by_author.items():
			# set total_commits in every ocurrence of contributor inside commits_by_author dictionary
			contributor[1].total_commit = total_commits
		self._total_commits = total_commits

	@property
	def total_java_files(self):
		return self._total_java_files

	@total_java_files.setter
	def total_java_files(self, total_java_files):
		for contributor in self._commits_by_author.items():
			contributor[1].total_file = total_java_files
		self._total_java_files = total_java_files

	@property
	def total_loc(self):
		return self._total_loc

	@total_loc.setter
	def total_loc(self, total_loc):
		for contributor in self._commits_by_author.items():
			# set total_commits in every ocurrence of contributor inside commits_by_author dictionary
			contributor[1].total_loc = total_loc
		self._total_loc = total_loc
